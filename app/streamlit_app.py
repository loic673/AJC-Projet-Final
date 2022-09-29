import streamlit as st
import pymongo
from pymongo import MongoClient
import numpy as np
import pandas as pd
import plotly.express as px
import time
from wordcloud import WordCloud, STOPWORDS
import matplotlib.pyplot as plt
import random

client = MongoClient()
client = MongoClient("mongodb://yohancaillau:KahlanAmnell1@mongo:27017/")
print("connected to mongo")

st.set_page_config(
    page_title="Real-Time Project Big Data Dashboard",
    page_icon="✅",
    layout="wide",
)

# Set the title of the page
tit1, tit2,tit3 = st.columns(3)
with tit1:
    st.image("https://static.latribune.fr/full_width/101610/twitter-nouveau-logo.jpg")

with tit2:
    st.title("Analyse de sentiments à partir de tweets sur la coupe du monde")


with tit3:
    st.image("https://upload.wikimedia.org/wikipedia/fr/e/e3/2022_FIFA_World_Cup.svg")


print("page is set")

placeholder = st.empty()
start_button = st.empty()


def graph():
    with placeholder.container():
        
        def get_data():
            db = client.project_twitter
            items = db.tweet_data.find()
            items = list(items)  # make hashable for st.experimental_memo
            return items

        items = get_data()

        def get_data_df():
            db = client.project_twitter
            df = pd.DataFrame(list(db.tweet_data.find({})))
            df = df.astype({"_id": str})
            return df

        df = get_data_df()
        print(df.tail())

        keys = random.randint(0, 9999)
        sentiment_filter = [st.selectbox("Selectionner le sentiment", df["sentiment"].unique(), key=keys)] # Dropdown box to select sender
        
        def count_keyword(df):       
            #sentiment_filter = [st.selectbox("Selectionner le sentiment", df["sentiment"].unique())] # Dropdown box to select sender
            df_kw_count_selected_sender = df[df['sentiment'].isin(sentiment_filter)]
            result = df_kw_count_selected_sender['sentiment'].value_counts()
            return result
        
       # create three columns
        kpi1, kpi2, kpi3 = st.columns(3)
        kpi1.metric(
            label="Compte des sentiments",
            value= count_keyword(df)
        )

        # fill in those three columns with respective metrics or KPIs
        kpi2.metric(
            label="Moyenne de Polarité",
            value=round(np.mean(df['polarity']),3)
        )

        kpi3.metric(
            label="Moyenne de la Subjectivité",
            value=round(np.mean(df['subjectivity']),3)
        )
        
        # create two columns for charts
        fig_col1, fig_col2, fig_col3 = st.columns(3)


        with fig_col1:
            st.markdown("### Polarité au cours du temps")
            fig = px.line(df, x="date", y="polarity", color="sentiment")
            st.write(fig)
           
            
        with fig_col2:
            st.markdown("### Fréquence des sentiments")
            fig2 = px.histogram(data_frame=df, x="sentiment")
            st.write(fig2)

        with fig_col3:
            st.markdown("### Word Cloud")
            fig, ax = plt.subplots()        
            words = ' '.join(df['processed_text'])
            wordcloud = WordCloud(stopwords=STOPWORDS, background_color='white', width=800, height=640).generate(words)
            ax.imshow(wordcloud, interpolation = 'bilinear')
            ax.axis("off")
            st.write(fig)
            

        st.markdown("### Detailed Data View")
        st.dataframe(df.tail())
    
if start_button.button('Start',key='start'):
    start_button.empty()
    if st.button('Stop',key='stop'):
        pass
    while True:
        graph() 
        time.sleep(10)
