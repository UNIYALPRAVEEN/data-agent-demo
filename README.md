# Data agent demo

A small, complete data agent you can run on your laptop and read in one sitting.
It is the live demo from the DataVidhya video "What is a data agent, and will it replace data engineers?"

## The big picture

```
   You ask a question
          │
          ▼
   ┌──────────────┐   "run this SQL"    ┌──────────────┐   SQL    ┌────────────────────┐
   │   agent.py   │ ◀────────────────── │    Claude    │          │  warehouse.duckdb  │
   │  (our code)  │ ──────────────────▶ │  (the brain) │          │   (the raw data)   │
   └──────────────┘   the result        └──────────────┘          └────────────────────┘
          │                                                                 ▲
          └───────────── our code runs the SQL on DuckDB, read-only ───────┘

   Repeat until Claude has the answer:  PLAN → LOOK → WRITE → RUN → CHECK → ANSWER
```

- **Claude** decides what to do next. It never touches the data itself.
- **agent.py** is the middleman. It gives Claude a few tools, runs whatever tool Claude
  asks for, and sends the result back.
- **DuckDB** is the warehouse. One file, no server, opened read-only.

## Read the files in this order

| # | File | What it is | Explain it as |
|---|---|---|---|
| 1 | `warehouse.duckdb` + `explore_warehouse.py` | The data: a fake food delivery company. 6 tables, 1.7 lakh orders. The script shows you what is inside. | "This is our company's warehouse. Let's look inside." |
| 2 | `chatbot.py` | 27 lines. Sends the question to Claude with no tools and no data. | "A chatbot can only guess." |
| 3 | `agent.py` | About 100 lines of real code in 5 sections: settings, connect, tools, instructions, loop. | "An agent can look, run SQL and check." |
| 4 | `show.py` | Only the coloured boxes on screen. No logic. Skip it on camera. | "This just makes it pretty." |
| 5 | `dbt_project/` | The data team's work: clean tables, docs, tests and metric definitions. | "This is the context the agent was missing." |
| 6 | `answers.sql` + `check_answers.py` | The correct SQL for every question, to check the agent. | "Never trust the agent blindly." |
| – | `build_warehouse.py` | Generates the fake data. Commented, but you never need to run it. | "Just a data generator." |
| – | `mcp/` | The no-code version: Claude Desktop connected to the same file through MCP. | "Same idea, no code." |

## The tables

| Table | One row per | Watch out |
|---|---|---|
| `cities` | city | |
| `restaurants` | restaurant | has a `city_id`, so city comes through here |
| `customers` | customer | |
| `orders` | order | `amount` includes GST and is before the promo. A refunded order still says `delivered`. |
| `order_taxes` | order | the GST for each order |
| `refunds` | refunded order | |

**Revenue** at this company = delivered and not refunded orders, after promo discount, without GST.
That rule is not written anywhere in these tables. It only exists in `dbt_project/`. That is the whole point of the demo.

## Look at the database

Before the agent touches the data, look at it yourself. Three ways, pick one.

**1. In the terminal (easiest)**

```bash
python explore_warehouse.py            # every table: rows, columns, what one row means, how they connect
python explore_warehouse.py orders     # one table: columns + 5 sample rows (any table name works)
python explore_warehouse.py traps      # the 3 traps that make "revenue" tricky, shown with real rows
```

**2. In your browser, with the DuckDB UI**

```bash
python explore_warehouse.py ui         # then open http://localhost:4213
```

You get a table browser on the left and a SQL notebook on the right. Click `warehouse` → `main`
to see the tables, or write SQL in a cell, for example:

```sql
SELECT status, COUNT(*) FROM orders GROUP BY status;
```

The script opens the warehouse read-only, so you can keep the UI open while the agent runs.
The UI downloads its web files from ui.duckdb.org the first time, so you need internet. Press
Enter in the terminal to stop it. (Avoid `duckdb -ui warehouse.duckdb`: that locks the file and
the agent can no longer open it.)

**3. With the DuckDB command line** (install with `brew install duckdb`)

```bash
duckdb -readonly warehouse.duckdb
```
```sql
SHOW TABLES;              -- list the tables
DESCRIBE orders;          -- columns and types
SUMMARIZE orders;         -- min, max, nulls and distinct values for every column
FROM orders LIMIT 5;      -- a few rows
.quit
```

## Run it

```bash
# one time
python3 -m venv .venv && source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip3 install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...                      # Windows: set ANTHROPIC_API_KEY=...

# 1. chatbot vs agent
python chatbot.py "Why did our orders drop in Mumbai last week?"
python agent.py   "Why did our orders drop in Mumbai last week?"

# 2. the agent gets it right
python agent.py "How many orders did we get from Mumbai last month?"         # correct: 6,171

# 3. the agent gets it wrong
python agent.py "What was our revenue last month?"                           # correct: ₹78,09,309

# 4. the fix: give it the data team's definitions
pip install -r requirements-dbt.txt
cd dbt_project && dbt build --profiles-dir . && cd ..
python agent.py "What was our revenue last month?" --context

# check any number yourself
python check_answers.py
```

Add `--pause` to any `agent.py` command to stop after every step while you explain it.

The agent's "today" is fixed at 15 Oct 2026, so "last month" is always September 2026 and
"last week" is always 5 to 11 Oct 2026. The default model is `claude-sonnet-5-5`;
change it with `DATA_AGENT_MODEL=...`.

## The dbt project in one minute

```
raw tables (warehouse.duckdb)
   │  sources.yml           tells dbt where the raw tables are
   ▼
staging                     stg_orders: rename columns, bring in GST and refunds
   │                        stg_restaurants: add the city name
   ▼
marts                       fct_orders: one row per order, with net_revenue = the business rule
   │  schema.yml            descriptions + tests (the agent reads these in --context mode)
   ▼
semantic layer              semantic_models.yml: revenue, orders, cancellation rate... defined once
```

Query a metric straight from the semantic layer:

```bash
cd dbt_project
export DBT_PROFILES_DIR=.
mf query --metrics revenue --group-by metric_time__month --start-time 2026-09-01 --end-time 2026-09-30
```

All data is synthetic, generated with a fixed seed. Names and numbers are not real.
