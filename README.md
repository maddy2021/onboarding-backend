## Part 8 Local Setup

1. `pip install poetry`
2. Install dependencies `cd` into the directory where the `pyproject.toml` is located then `poetry install`
3. Revision the version of the database `alembic revision --autogenerate -m "initial db"`
4. Run the DB migrations via poetry `poetry run ./prestart.sh` (only required once)
5. Run the FastAPI server via poetry `poetry run ./run.sh`
6. Open http://localhost:8001/


To add table
1. Create a file forr model. lets say example user.py -> which have Fields regarding user
2. add that models entry in db/base.py
3. Add schema regarding the model for DB and CRUD
4. For every model we need to make crud operation add that in CRUD model if you have same functionality like base model keep it as it is
5. run command to update database
  -> alembic revision --autogenerate -m "your message"
  -> alembic upgrade head