from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv
load_dotenv()
print(create_engine(os.environ["DATABASE_URL"]).connect().execute(text("select 1")).scalar())
