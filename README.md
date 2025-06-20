# mongodb_project

- [Description](#description)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Usage](#usage)
- [Contributing](#contributing)

## Description
The goal of this project is to collect data from the Riot Games API, then put it into collections inside MongoDB, do some computation using Aggregate, and visualize it using Streamlit.

![LoL dashboard](/images/image.png)

## Prerequisites

1. Python
2. RIOT_API_KEY. Sign up at [Riot Developer Page](https://developer.riotgames.com/).
3. MongoDB and MongoDB Connection String URI
## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/truongvude/mongodb_project.git
cd mongodb_project
mkdir logs
```

### 2. Set up a Virtual Environment:

```bash
python -m venv .venv
source .venv/bin/activate   # For Unix/macOS
# or
.venv\Scripts\activate      # For Windows
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Create your .env file using the provided example:
```bash
mv .env_example .env
```
Then open .env and insert your Riot API key and MongoDB Connection String URI and your MongoDB database:
```bash
nano .env   # Or use any text editor of your choice
```

## Usage

### 1. Run `main.py` to fetch data from API

```bash
python src/main.py
```

### 2. Run `aggregation.py` to Aggerate collection
```bash
python src/aggregate.py
```

### 3. Run `app.py` with Streamlit
```bash
streamlit run src/app.py
```

## Contributing

Pull requests are welcome. For major changes, please open an issue first
to discuss what you would like to change.

Please make sure to update tests as appropriate.