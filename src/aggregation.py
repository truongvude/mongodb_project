# Import 
import os
from pymongo import MongoClient
from dotenv import load_dotenv

# Load env variables
load_dotenv()

MONGO_URI = os.getenv("CONNECTION_STRING_URI")
DB_NAME = os.getenv("DB_NAME")

# --- Kết nối MongoDB ---
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
match_detail = db["match_detail"]
participant = db["participant"]


# Unwind pipeline
unwind_pipeline = [
  { 
    "$unwind": "$info.participants" 
  },
  { 
    "$project": {
       "_id": 0,
       "matchId": "$metadata.matchId" ,
       "participant": "$info.participants"
       } 
  },
  {
    "$out": "participant" 
  }
]

# Update pipeline
# Chuyển đổi các trường đặc biệt trong document thành dạng chữ (Update)
update_pipeline = [
 {
    "$set": {
      "participant.championTransform": {
        "$switch": {
          "branches": [
            {
              "case": { "$eq": ["$participant.championTransform", 1] },
              "then": "Slayer"
            },
            {
              "case": { "$eq": ["$participant.championTransform", 2] },
              "then": "Assassin"
            }
          ],
          "default": "$participant.championTransform"
        }
      }
    }
  },
  {
    "$merge": {
      "into": "participant",
      "whenMatched": "merge",
      "whenNotMatched": "insert"
    }
  }
]

# Xóa các bản ghi đầu hàng sớm
delete_pipeline = {"participant.gameEndedInEarlySurrender": True}

def main():
    # Thực hiện tách các giá trị trong mảng thành collection mới
    match_detail.aggregate(unwind_pipeline)

    # Cập nhật các trường đặc biệt thành dạng chữ
    participant.aggregate(update_pipeline)

    # Xóa các documents đầu hàng sớm (ngoại lai)
    participant.delete_many(delete_pipeline)

    client.close()
    
if __name__ == "__main__":
    main()
