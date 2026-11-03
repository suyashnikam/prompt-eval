# prompt_eval

**Find out how good your AI prompt is, and get a better version of it.**

You paste a prompt like *"pls write email to client"*. Claude scores it out of 10, explains what's missing, and rewrites it into a clear, detailed prompt you can use in ChatGPT, Claude, Gemini or any other AI tool.

The project has two tools:

1. **Prompt Scorer**: a web page where you paste a prompt and get a score and an improved version. No technical knowledge needed to use it.
2. **Eval harness**: a command-line tool for developers. It runs a prompt against a list of test questions and tells you how many answers were correct.

> This is a proof of concept for learning and experimenting. It runs on your own computer.

---

## What you need

- [ ] **Python 3.10 or newer.** Check by running `python3 --version`. [Download Python](https://www.python.org/downloads/) if needed.
- [ ] **A way to use Claude.** Pick **one**:
  - **Option A: Anthropic API key** (easiest). Takes about 2 minutes.
  - **Option B: Amazon Bedrock**. Use this if you already have an AWS account.

Either option costs money per use. Each scored prompt or test question is one paid call to Claude, billed to your own account.

### Option A: Get an Anthropic API key

1. Sign up at [console.anthropic.com](https://console.anthropic.com).
2. Add a payment method under **Billing**.
3. Open **API Keys**, click **Create Key**, and copy the key. It starts with `sk-ant-`.

### Option B: Set up Amazon Bedrock

1. Sign in to the [AWS console](https://console.aws.amazon.com) and open **Amazon Bedrock**.
2. Pick a region where Claude is available, for example **US East (N. Virginia) / `us-east-1`**.
3. Make sure you can use **Claude Opus 5** in that region. Check **Model access** or the **Model catalog** page. The first time you use an Anthropic model, AWS may ask you to fill in a short use-case form.
4. Make sure your AWS user is allowed to call Bedrock models. On a personal account, the `AmazonBedrockFullAccess` policy covers this.
5. Install the [AWS CLI](https://aws.amazon.com/cli/) and log in with `aws configure` (or `aws sso login` if you use SSO).

---

## Install (one time)

**Step 1: Download the code**

```bash
git clone <this-repo-url>
cd prompt_eval
```

**Step 2: Create a virtual environment and install the packages**

Mac / Linux:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Windows:
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

**Step 3: Add your credentials**

Copy the example settings file:

```bash
cp .env.example .env        # Windows: copy .env.example .env
```

Open the new `.env` file in any text editor. Its contents should be **one** of these:

If you chose **Option A** (Anthropic API key):
```
ANTHROPIC_API_KEY=sk-ant-your-real-key
```

If you chose **Option B** (Amazon Bedrock), remove the `ANTHROPIC_API_KEY` line and write:
```
AWS_REGION=us-east-1
AWS_PROFILE=your-aws-profile
```
(Leave out `AWS_PROFILE` if you only have the default AWS profile.)

The code checks `.env` automatically: if it finds `ANTHROPIC_API_KEY`, it uses the Anthropic API, and otherwise it uses Bedrock. `.env` is git-ignored, so your keys stay on your computer.

---

## Use the Prompt Scorer

**1. Start the app**

```bash
python app.py
```

Leave this terminal window open while you use the app.

**2. Open http://127.0.0.1:5050 in your browser**

**3. Paste a prompt and click "Score this prompt"**

After a few seconds you'll see:

| Section | What it tells you |
|---|---|
| **Overall score** | 1 to 10. Green is good, yellow is OK, red needs work. |
| **Scorecard** | A score for each of six things a good prompt needs (see below). |
| **What's working** | What your prompt already does well. |
| **Improvement points** | Exactly what's missing. |
| **Improved prompt** | A rewritten version. Click **Copy** and use it in any AI tool. |
| **Technical details** | The raw data, model used and tokens used, for the curious. |

**The six things a good prompt needs:**

| Category | The question it answers |
|---|---|
| Clarity | Is it obvious what you're asking for? |
| Specificity | Does it include concrete details, or is it vague? |
| Context | Does it explain the background, audience or role? |
| Structure | Does it say what format the answer should be in? |
| Constraints | Does it mention tone, length, or what to avoid? |
| Actionability | Could an AI start right away without guessing? |

**4. Stop the app** by pressing `Ctrl + C` in the terminal.

---

## Use the Eval harness (for developers)

The Eval harness checks whether a prompt gives the **right answers**. You write test questions with the answers you expect, and it tells you how many it got right.

### Try the included example

```bash
python runner.py --prompt prompts/qa_assistant.yaml --test-cases test_cases/sample.yaml
```

You'll see something like:

```
[PASS] capital_france
[PASS] capital_japan
[PASS] capital_australia
[PASS] explain_recursion

4/4 passed (100%)
Report written to reports/run_<timestamp>.json
```

The full results, including every answer, are saved in that JSON file.

### How it's set up

**The prompt being tested** lives in `prompts/qa_assistant.yaml`:

```yaml
name: qa_assistant
system: "You are a helpful, concise assistant. Answer in one sentence."
template: "{input}"      # {input} is replaced by each test question
```

**The test questions** live in `test_cases/sample.yaml`:

```yaml
- id: capital_france
  input: "What is the capital of France?"
  expected: "Paris"
  grader: contains        # passes if "Paris" appears anywhere in the answer

- id: explain_recursion
  input: "Explain recursion in one sentence."
  rubric: "Correctly explains recursion and is about one sentence long."
  grader: llm_judge       # a second Claude call grades the answer against the rubric
```

### The three ways to grade an answer

| Grader | Passes when | Needs |
|---|---|---|
| `exact_match` | The answer is exactly the expected text | `expected` |
| `contains` | The expected text appears somewhere in the answer | `expected` |
| `llm_judge` | Claude scores the answer 4 or 5 out of 5 against your rubric | `rubric` |

### Test your own prompt

1. Copy `prompts/qa_assistant.yaml` to a new file and change the `system` text.
2. Copy `test_cases/sample.yaml` to a new file and write your own questions.
3. Run it:
   ```bash
   python runner.py --prompt prompts/my_prompt.yaml --test-cases test_cases/my_tests.yaml
   ```
4. To find out which of two prompts is better, run both against the same test file and compare the pass rates.

### Optional flags

| Flag | What it does | Default |
|---|---|---|
| `--model` | Which Claude model answers the questions | `claude-opus-5` |
| `--judge-model` | Which Claude model grades `llm_judge` questions | `claude-opus-5` |
| `--out` | Where to save the report | `reports/run_<timestamp>.json` |

---

## How it works

Both tools ask Claude to reply in a fixed JSON format (Claude's **structured outputs** feature). The format is defined in `prompt_scorer.py` for the scorer and in `graders/llm_judge.py` for the judge. It's like handing Claude a form to fill in: every field must be filled, nothing extra can be added, and the reply always has the same shape. So the app never has to guess how to read Claude's answer.

To use a different model, change the names in `config.py`. Write the model name in its plain form (for example `claude-opus-5`). The code adds the extra `anthropic.` prefix Bedrock needs on its own.

---

## Project files

| File / folder | What it is |
|---|---|
| `app.py` | Starts the Prompt Scorer web app |
| `prompt_scorer.py` | The scoring instructions and the JSON format Claude must reply in |
| `templates/index.html` | The web page you see in the browser |
| `runner.py` | Runs the Eval harness |
| `graders/` | The three grading methods |
| `prompts/` | Prompts to test |
| `test_cases/` | Test questions and expected answers |
| `reports/` | Eval results are saved here (not uploaded to GitHub) |
| `client.py` | Chooses between the Anthropic API and Bedrock |
| `config.py` | Which Claude models to use |
| `.env.example` | Template for your credentials. Copy it to `.env`. |

---

## Troubleshooting

| You see | What to do |
|---|---|
| `No ANTHROPIC_API_KEY set, and no AWS_REGION ...` | The `.env` file is missing or empty. Repeat **Install, Step 3**. |
| `command not found: python` | Use `python3` instead (Mac/Linux). |
| `ModuleNotFoundError` | The virtual environment isn't active. Run `source .venv/bin/activate` (Windows: `.venv\Scripts\activate`), then try again. |
| `401` or "authentication" error | Your API key is wrong, or your AWS login has expired. For AWS, run `aws sso login` or `aws configure` again. |
| Bedrock "access denied" or "model not found" | Claude Opus 5 isn't enabled for your account in that region. See **Option B, step 3**. |
| The page says "Scoring failed, please try again." | Look at the terminal where `app.py` is running. The real error is printed there. |
| `Address already in use` | Something else is using port 5050. Close it, or change `port=5050` at the bottom of `app.py`. |

---

## A note on safety

The web app is meant to run **only on your own computer**. It has no login and no usage limits, and every request costs money on your account. Don't put it on a public server without adding those first.
