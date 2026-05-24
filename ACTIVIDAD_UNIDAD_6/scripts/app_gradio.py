"""App Gradio para la U6: chat con el LLM local (Gemma) y vista del grafo de la red.

Replica la lógica de DataExtractor.chat_local_llm para el despliegue. Se lanza con:
    python scripts/app_gradio.py
"""

import json
import os
from pathlib import Path

import gradio as gr
import torch
from dotenv import load_dotenv
from transformers import pipeline

ROOT = Path(__file__).resolve().parent.parent
GRAFO = ROOT / "data" / "gold" / "network_graph.png"
METRICAS = ROOT / "data" / "gold" / "network_metrics.json"

load_dotenv(ROOT / ".env")
MODELO = os.getenv("LLM_MODEL", "google/gemma-4-E2B-it")
DEVICE = "mps" if torch.backends.mps.is_available() else "cpu"


def construir_contexto():
    brevedad = ("Responde en español de forma concisa y directa, en 2-3 párrafos como máximo; "
                "no te extiendas más de lo necesario.")
    base = ("Eres un analista de redes sociales. Estás ayudando a interpretar un grafo de "
            "menciones construido a partir de tweets sobre criptomonedas.")
    if not METRICAS.exists():
        return f"{base} {brevedad}"
    m = json.loads(METRICAS.read_text())
    top = ", ".join("@" + u["usuario"] for u in m.get("top_centralidad", []))
    return (
        f"{base} Estos son los datos de la red:\n"
        f"- Usuarios (nodos): {m['num_nodos']}\n"
        f"- Interacciones (aristas): {m['num_aristas']}\n"
        f"- Comunidades detectadas (Louvain): {m['num_comunidades']}\n"
        f"- Usuarios más influyentes por centralidad: {top}\n"
        f"Apóyate en estos datos. {brevedad}"
    )


CONTEXTO = construir_contexto()
CONTEXTO_MSGS = [
    {"role": "user", "content": CONTEXTO},
    {"role": "assistant", "content": "De acuerdo, tengo el contexto de la red de menciones. ¿Qué quieres saber?"},
]

print(f"Cargando {MODELO} en {DEVICE} (la primera vez descarga los pesos)...")
llm = pipeline("text-generation", model=MODELO, device=DEVICE,
               dtype=torch.bfloat16, token=os.getenv("HF_TOKEN"))


def responder(mensaje, historial):
    mensajes = CONTEXTO_MSGS + historial + [{"role": "user", "content": mensaje}]
    salida = llm(mensajes, max_new_tokens=512)
    return salida[0]["generated_text"][-1]["content"]


with gr.Blocks(title="U6 · Red + LLM") as demo:
    gr.Markdown("# Análisis de redes sociales + chat con Gemma")
    with gr.Row():
        with gr.Column(scale=1):
            if GRAFO.exists():
                gr.Image(value=str(GRAFO), label="Grafo de menciones")
            else:
                gr.Markdown("_Ejecuta el notebook para generar el grafo (`network_graph.png`)._")
        with gr.Column(scale=1):
            gr.ChatInterface(responder,
                             description="Pregunta al modelo sobre la red de menciones de cripto.")

if __name__ == "__main__":
    demo.launch()
