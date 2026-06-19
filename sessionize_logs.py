import pandas as pd
from sqlalchemy import create_engine

INPUT_PATH = "data/cleaned_logsanddomains.log"
NOISE_DOMAINS_PATH = "data/noise_domains.txt"
OUTPUT_PATH = "data/sessions.csv"

SESSION_THRESHOLD_SECONDS = 15

# Инициализируем движок БД. Локальный хост и дефолтный пароль для портфолио — ок,
# главное, что в реальном проде мы бы убрали это в конфиг/.env.
engine = create_engine("postgresql://postgres:1488@localhost:5432/traffick", echo=True)

# Load manually excluded domains.
with open(NOISE_DOMAINS_PATH, "r", encoding="utf-8") as f:
    noise_domains = [line.strip() for line in f if line.strip()]

# Load domain-normalized logs from the previous ETL step.
df = pd.read_csv(INPUT_PATH, encoding="utf-8")

# Remove manually selected noisy domains.
df = df[~df["clear_names"].isin(noise_domains)].copy()

# Build a single datetime column from date and time.
df["datetime"] = pd.to_datetime(df["date"] + " " + df["time"])

# Keep only columns needed for sessionization and analysis.
df = df[
    [
        "datetime",
        "email",
        "src_ip",
        "src_port",
        "protocol",
        "clear_names",
        "domain",
        "port",
    ]
]

# Sort events before calculating time gaps.
df = df.sort_values(["email", "clear_names", "datetime"])

# Calculate time difference between current and previous request.
df["time_diff"] = (
    df.groupby(["email", "clear_names"])["datetime"]
    .diff()
    .dt.total_seconds()
)

# Mark a new session when the gap between requests is greater than threshold.
df["new_session"] = df["time_diff"] > SESSION_THRESHOLD_SECONDS
df["new_session"] = df["new_session"].fillna(True)

# Create session IDs as cumulative sum of new_session flags.
df["session_id"] = (
    df.groupby(["email", "clear_names"])["new_session"]
    .cumsum()
)

# Aggregate raw requests into user-domain sessions.
sessions = (
    df.groupby(["email", "clear_names", "session_id"])
    .agg(
        session_start=("datetime", "min"),
        session_end=("datetime", "max"),
        requests=("datetime", "count"),
    )
    .reset_index()
)

# Calculate session duration in seconds.
sessions["session_time"] = (
    sessions["session_end"] - sessions["session_start"]
).dt.total_seconds()

# Remove one-second-zero-duration noise.
sessions_filtered = sessions[
    (sessions["session_time"] >= 1)
    & (sessions["requests"] >= 1)
].copy()


def session_export(df_to_export):
    # Сначала выводим подсказку, чтобы пользователь понимал, что вводить
    print("Input format: 1 to CSV, 2 to Excel, 3 to SQL")
    x = int(input())
    
    if x == 1:
        # Исправлено расширение на .csv для корректного чтения программами
        df_to_export.to_csv("data/sessions.csv", index=False, encoding="utf-8")
        print("Successfully saved to data/sessions.csv")
    elif x == 2:
        # Исправлено расширение на .xlsx для Excel формата
        # (Понадобится библиотека openpyxl: pip install openpyxl)
        df_to_export.to_excel("data/sessions.xlsx", index=False)
        print("Successfully saved to data/sessions.xlsx")
    elif x == 3:
        # Изменено на 'append', чтобы не удалять существующую таблицу и её структуру
        df_to_export.to_sql(
            name='my_table',          # Имя таблицы в базе данных
            con=engine,               # Объект подключения (engine)
            if_exists='append',       # Дописываем строки в конец таблицы
            index=False               # Не записываем индексы DataFrame
        )
        print("Successfully exported to PostgreSQL table 'my_table'")


# Вызываем функцию и передаем в нее наш отфильтрованный датасет сессий
session_export(sessions_filtered)

# Basic run summary.
print(f"\nRaw rows after noise filtering: {len(df)}")
print(f"Sessions created: {len(sessions_filtered)}")
print(f"Unique users: {sessions_filtered['email'].nunique()}")
print(f"Unique domains: {sessions_filtered['clear_names'].nunique()}")