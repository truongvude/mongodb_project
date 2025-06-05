import os
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from pymongo import MongoClient
import pandas as pd
import altair as alt
from dotenv import load_dotenv

st.set_page_config(
    page_title="League of Legends Dashboard",
    layout="wide",
    initial_sidebar_state="expanded")

alt.themes.enable("dark")

load_dotenv()

# --- Cấu hình MongoDB ---
MONGO_URI = os.getenv("CONNECTION_STRING_URI")
DB_NAME = os.getenv("DB_NAME")

# --- Kết nối MongoDB ---
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
match_detail = db["match_detail"]
participant = db["participant"]


# --- Pipeline Aggregation ---
calculation_pipeline = [
    {
        "$group": {
            "_id": "$participant.championName",
            
            # Tính trung bình và tối đa damage
            "average_damage_to_champions": {"$avg": "$participant.totalDamageDealtToChampions"},
            "average_damage_to_objectives": {"$avg": "$participant.damageDealtToObjectives"},
            "average_damage_to_buildings": {"$avg": "$participant.damageDealtToBuildings"},
            "average_kills": {"$avg": "$participant.kills"},
            "average_deaths": {"$avg": "$participant.deaths"},
            "average_assists": {"$avg": "$participant.assists"},
            "average_damage_taken": {"$avg": "$participant.totalDamageTaken"},
            "average_heal": {"$avg": "$participant.totalHeal"},

            "max_damage_to_champions": {"$max": "$participant.totalDamageDealtToChampions"},
            "total_pentakills": {"$sum": "$participant.pentaKills"},
            "total_kills": {"$sum": "$participant.kills"},
            "total_deaths": {"$sum": "$participant.deaths"},
            "total_assists": {"$sum": "$participant.assists"},
            "total_minions": {"$sum": "$participant.totalMinionsKilled"},
            # Tính số trận thắng và tổng số trận
            "wins": {
                "$sum": {
                    "$cond": [{"$eq": ["$participant.win", True]}, 1, 0]
                }
            },
            "total_games": {"$sum": 1}
        }
    },
    {
    "$addFields": {
      "kda": {
        "$cond": [
          { "$eq": ["$total_deaths", 0] },
          { "$add": ["$total_kills", "$total_assist"] },
          {
            "$divide": [
              { "$add": ["$total_kills", "$total_assists"] },
              "$total_deaths"
            ]
          }
        ]
      }
    }
  }
]


# --- Truy vấn dữ liệu ---
result = list(participant.aggregate(calculation_pipeline))

# --- Hiển thị bằng Streamlit ---
st.title("Thống kê thông tin tướng")

# Chuyển sang DataFrame
df = pd.DataFrame(result)
df = df.rename(columns={"_id": "Champion"})


def get_participant_champion(championName):
    champion_participant = df.loc[df["Champion"] == championName, :]
    return champion_participant

def plot_winrate(champion_participant, title):
    win_rate = round(float(champion_participant["wins"] / champion_participant["total_games"]), 2)
    percent = [win_rate, 1 - win_rate]
    labels = ['Win', 'Lose']
    colors = ['green', 'red']

    fig = go.Figure(
        data=[go.Pie(
            labels=labels,
            values=percent,
            marker=dict(colors=colors),
            textinfo='label+percent',
            title=title  # Nếu muốn biểu đồ donut
        )]
    )

    fig.update_layout(title=f"Win Rate: {win_rate * 100:.0f}%", width=400, height=400)
    st.plotly_chart(fig)

def plot_top_chart(attribute, n, title, color, ascending=True):
    top_champion = df.sort_values(attribute, ascending=ascending).iloc[:n][["Champion", attribute]]
    
    fig = px.bar(
        top_champion,
        x="Champion",
        y=attribute,
        title=title,
        color=attribute,
        color_continuous_scale=color
    )

    fig.update_layout(xaxis_tickangle=-45, width=600, height=400)
    st.plotly_chart(fig)

def plot_chart(champion, array_attributes, title, color):
    # Lọc dữ liệu của champion được chọn
    champion_participant = df[df["Champion"] == champion]

    if champion_participant.empty:
        st.warning("Không tìm thấy dữ liệu cho tướng đã chọn.")
        return

    # Lấy các giá trị thuộc tính từ DataFrame
    data = {
        "Thuộc tính": array_attributes,
        "Giá trị": [float(champion_participant[attr]) for attr in array_attributes]
    }
    chart_df = pd.DataFrame(data)
    # Vẽ biểu đồ bar với nhiều cột
    fig = px.bar(
        chart_df,
        x="Thuộc tính",
        y="Giá trị",
        title=title,
        color="Giá trị",
        color_continuous_scale=color
    )
    fig.update_layout(xaxis_tickangle=-45, width=600, height=400)
    st.plotly_chart(fig)

list_champion = sorted(df["Champion"].to_list())
champion = st.selectbox("Choose champion", list_champion)


st.dataframe(df) # Luôn hiển thị tất cả các tướng

if st.button("Show stats"):
    champion_participant = get_participant_champion(champion)
    try:
        st.dataframe(champion_participant, use_container_width=True)

        col1, col2, col3, col4 = st.columns([2,2,2,2])

        with col1:
            st.metric(label="Số trận thắng", value=champion_participant["wins"])
            st.metric(label="Tổng số trận", value=champion_participant["total_games"])
            plot_winrate(champion_participant, f"Tỷ lệ thắng của tướng {champion}")
        with col2:
            st.metric(label="K/DA trung bình", value=round(champion_participant["kda"], 2))
            st.metric(label="Tổng số mạng hạ gục", value=champion_participant["total_kills"])
            plot_chart(champion, ["average_damage_to_champions", "average_damage_taken", "average_heal"], f"Thông số của tướng {champion}", color="Magma")
        with col3:
            st.metric(label="Số lần bị hạ gục", value=champion_participant["total_deaths"])
            st.metric(label="Tổng số mạng hỗ trợ", value=champion_participant["total_assists"])
            plot_top_chart("total_pentakills", 5, "Top 5 tướng đạt pentakill nhiều nhất",ascending=False, color="Blues")
        with col4:
            st.metric(label="Tổng số lính tiêu diệt", value=champion_participant["total_minions"])
            st.metric(label="Tổng số lần đạt được pentakill", value=champion_participant["total_pentakills"])
            plot_top_chart("average_damage_to_champions", 5, "Top 5 tướng có sát thương trung bình lên tướng cao nhất",ascending=False, color="Reds")

    except:
        st.text("Chọn tướng")