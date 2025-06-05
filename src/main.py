# Import thư viện
import logging
import os
from dotenv import load_dotenv
import pymongo
import requests
import time
from datetime import datetime
from typing import List, Dict

# Loading key
load_dotenv()
API_KEY = os.getenv("RIOT_API_KEY")

# Chỉ định thời gian lấy dữ liệu
end_time = int(datetime.now().timestamp())
start_time = end_time - 24*60*60*30

# Kết nối đến mongodb và khởi tạo collections
client = pymongo.MongoClient(os.getenv("CONNECTION_STRING_URI"))
mydb = client["riot_db"]

# Cấu hình log
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("logs/riot_data_pipeline.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

# Hàm lấy danh sách người chơi theo bậc xếp hạng
def get_player_by_rank(rank: str, queue: str, api_key: str, region: str = "vn2") -> List[Dict]:
    """
    Lấy danh sách người chơi theo bậc xếp hạng và hàng chờ.\n
    :param rank: Bậc xếp hạng (Bao gồm: master, grandmaster, challenger).
    :param api_key: API key của Riot Games.
    :param queue: Hàng chờ xếp hạng (Bao gồm: RANKED_SOLO_5x5, RANKED_FLEX_SR).
    :param region: Khu vực của người chơi
    :return: Thông tin của các người chơi trong bậc xếp hạng.
    """
    try:
        response = requests.get(f"https://{region}.api.riotgames.com/lol/league/v4/{rank}leagues/by-queue/{queue}?api_key={api_key}")
        response.raise_for_status()

        data = response.json()
        return data.get("entries", [])
    except requests.exceptions.RequestException as e:
        logging.warning(f"Lỗi khi gọi API: {e}")
        return []


# Hàm lấy danh sách trận đấu của người chơi
def get_player_matches(puuid, queue, type, start_time, end_time, api_key, start=0, count=20, region="sea") -> Dict:
    """
    Lấy thông tin các trận đấu của người chơi.\n
    :param puuid: Mã định danh người chơi.
    :param queue: Hàng chờ xếp hạng .
    :param type: Kiểu trận đấu (Bao gồm: ranked, normal, tourney, turtorial).
    :param start_time: Thời gian bắt đầu (tính theo UNIX time).
    :param end_time: Thời gian kết thúc (tính theo UNIX time).
    :param start: Start index (số trận bắt đầu).
    :param count: Số lượng mã trận đấu cần lấy (từ 0 đến 100).
    :param api_key: API key của Riot Games.
    :param region: Khu vực của người chơi.
    """
    try:
        response = requests.get(f"https://{region}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?startTime={start_time}&endTime={end_time}&queue={queue}&type={type}&start={start}&count={count}&api_key={api_key}")
        response.raise_for_status()
        data = response.json()
        return {
            "puuid": puuid,
            "matches": data,
            "type": type,
            "insertedAt": datetime.now().strftime("%Y-%m-%d")
        }
    except requests.exceptions.RequestException as e:
        logging.warning(f"Lỗi khi gọi API: {e}")
        return {
            "puuid": puuid,
            "matches": [],
            "type": type,
            "insertedAt": datetime.now().strftime("%Y-%m-%d"),
            "error": str(e)
        }

# Hàm lấy thông tin trận đấu theo mã trận đấu
def get_match_info(match_id, api_key, region="sea") -> Dict:
    """
    Lấy thông tin trận đấu.\n
    :param match_id: Mã trận đấu (Có dạng: VN2_XXXXXXXXX)
    :param api_key: API key của Riot Games.
    :param region: Khu vực của người chơi.
    :return: Thôn tin trận đấu, bao gồm metadata và info.
    """
    try:
        response = requests.get(f"https://{region}.api.riotgames.com/lol/match/v5/matches/{match_id}?api_key={api_key}")
        response.raise_for_status()
        data = response.json()

        return data
    except requests.exceptions.RequestException as e:
        logging.warning(f"Lỗi khi gọi API: {e}")
        return {}


def main():
    # Khởi tạo collections
    player = mydb["player1"]
    matches = mydb["matches1"]
    match_detail = mydb["match_detail1"]

    # Lấy danh sách người chơi
    list_players = get_player_by_rank("challenger", "RANKED_SOLO_5x5", API_KEY)
    player.insert_many(list_players)
    logging.info("Tạo và chèn thành công dữ liệu người chơi!")

    # Lấy danh sách trận đấu của các người chơi
    for puuid in player.distinct("puuid"):
        time.sleep(1.5)
        player_matches = get_player_matches(puuid, 420, "ranked", start_time, end_time, API_KEY, count=50)
        matches.insert_one(player_matches)
        logging.info(f"Thêm thành công dữ liệu trận đấu của người chơi {puuid}")

    # Lấy thông tin trận đấu
    for match_id in matches.distinct("matches"):
        time.sleep(1.5)
        match_info = get_match_info(match_id, API_KEY)
        match_detail.insert_one(match_info)
        logging.info(f"Thêm thành công thông tin trận đấu {match_id}")

if __name__ == "__main__":
    main()

