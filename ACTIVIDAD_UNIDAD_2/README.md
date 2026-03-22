# Actividad Práctica U2 · Extracción y Tratamiento de Datos

Práctica de la asignatura **Búsqueda y Análisis de la Información** (BAIN) · UTAD.

## Dataset

Dataset **Bitcoin Tweets** de Kaggle, archivo `Bitcoin_tweets_dataset_2.csv`:
https://www.kaggle.com/datasets/kaushiksuresh147/bitcointweets

Contiene tweets relacionados con Bitcoin con información de texto, fecha y usuario.

## Qué hace el notebook

1. **Carga** el CSV con Polars y hace una exploración básica del dataset
2. **Guarda** los datos en CSV con codificación UTF-8
3. **Limpia** el texto de cada tweet (URLs, menciones, emojis, espacios)
4. **Extrae hashtags** y calcula frecuencias globales, por usuario y por fecha
5. **Visualiza** los resultados con gráficas de barras, evolución temporal y una wordcloud

Todo el procesamiento está centralizado en la clase `DataExtractor`.

## Cómo ejecutarlo

**Requisitos:** Python 3.10+

```bash
# Instalar dependencias
pip install -r requirements.txt

# Abrir el notebook
jupyter notebook Actividad_Practica_U2_DataExtractor.ipynb
```

Asegúrate de tener el archivo `Bitcoin_tweets_dataset_2.csv` dentro de la carpeta `data/`.
