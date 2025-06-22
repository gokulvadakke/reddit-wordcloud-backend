from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import asyncpraw
from wordcloud import WordCloud, STOPWORDS
import io
import base64

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    query: str

@app.post("/api/analyze")
async def analyze(req: QueryRequest):
    reddit = asyncpraw.Reddit(
        client_id="OiR6pK8OvA679VfKYjAETw",
        client_secret="cShA-iVkLX6C8rd5jbc2RI0qXxqNxQ",
        user_agent="reddit-wordcloud-app"
    )

    query = req.query.lower()
    collected_text = ""

    try:
        subreddit = await reddit.subreddit("all")
        async for submission in subreddit.search(query, limit=10):
            collected_text += f"{submission.title} {submission.selftext} "

            await submission.load()
            await submission.comments.replace_more(limit=0)
            for comment in submission.comments[:3]:
                collected_text += f"{comment.body} "

        if not collected_text.strip():
            return {"image": ""}

        # 🔸 Define custom stopwords
        custom_stopwords = set(STOPWORDS)
        custom_stopwords.add(query)  # Remove the search term itself

        # Add any extra words you want to filter out
        blacklist = {"https", "http", "www", "com", "imgur", "like", "get"}
        custom_stopwords.update(blacklist)

        # 🔸 Create the word cloud
        wc = WordCloud(
            width=800,
            height=400,
            background_color="white",
            stopwords=custom_stopwords
        ).generate(collected_text)

        img_io = io.BytesIO()
        wc.to_image().save(img_io, format="PNG")
        img_io.seek(0)
        encoded = base64.b64encode(img_io.read()).decode("utf-8")
        return {"image": encoded}

    except Exception as e:
        print(f"Error: {e}")
        return {"image": ""}
