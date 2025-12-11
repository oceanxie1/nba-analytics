# How IDs are Determined in the Database

## Auto-Incrementing Primary Keys

In your SQLAlchemy models, IDs are **automatically generated** by the database when you insert new records.

### How it works:

1. **Model Definition** (in `app/models.py`):
   ```python
   id = Column(Integer, primary_key=True, index=True)
   ```
   - `primary_key=True` tells SQLAlchemy this is the primary key
   - `Integer` means it's an integer type
   - The database (SQLite) automatically makes it **auto-incrementing**

2. **When you create a record**:
   ```python
   team = Team(name="Lakers", abbreviation="LAL", ...)
   db.add(team)
   db.commit()
   # At this point, team.id is automatically assigned by the database
   ```

3. **ID Assignment**:
   - First record gets `id = 1`
   - Second record gets `id = 2`
   - Third record gets `id = 3`
   - And so on...

4. **You don't specify the ID**:
   - You **never** set `id=` when creating records
   - The database handles it automatically
   - Even if you delete records, the IDs don't get reused (they keep incrementing)

### Example from your sample data:

```python
# When you added teams:
lakers = Team(name="Los Angeles Lakers", ...)  # No id specified
db.add(lakers)
db.commit()
# After commit, lakers.id = 1 (assigned automatically)

warriors = Team(name="Golden State Warriors", ...)  # No id specified
db.add(warriors)
db.commit()
# After commit, warriors.id = 2 (assigned automatically)
```

### Important Notes:

- **IDs are sequential**: 1, 2, 3, 4...
- **IDs are unique**: Each record gets a unique ID
- **IDs persist**: Even if you delete a record, its ID is gone forever (won't be reused)
- **You can't control IDs**: They're managed by the database

### If you need to see the ID after creation:

```python
db.add(new_record)
db.commit()
db.refresh(new_record)  # This reloads the record from DB, including the auto-generated ID
print(new_record.id)  # Now you can see the ID
```

