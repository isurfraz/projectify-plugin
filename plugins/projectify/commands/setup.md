---
description: Set up Projectify with a few skippable questions, then your workspace, first project and team
---

Set me up in Projectify using the Projectify tools. Keep every message short.

1. Call `act("get_onboarding")`. It returns the questions with their option labels, what I already answered and what is left. If I am a member joining a workspace, it lists only the short set; ask only those. If I already finished, show me what I answered and ask whether to change anything.
2. Ask me the questions that are left, one per message, with your multiple-choice tool (AskUserQuestion in Claude Code) where there are options, and in plain text for the one-line answers. Show the labels, never the values. Every question is skippable: offer "Skip" on each and "Skip all" once. Guess `kind` from my first answer and offer it first. The questions:
   1. working_on: "What are you working on first?" (one line)
   2. kind: "What kind of work is it?" (one of: app, website, marketing, shop, event, business, personal, other)
   3. role: "What's your role?" (one of: founder, developer, designer, pm, marketing, operations, freelancer, student, other)
   4. team_size: "How many people will work in it?" (one of: solo, 2_5, 6_20, 21_50, 50_plus)
   5. ai_use: "Which Claude do you use?" (several of: claude_code, claude_ai, claude_desktop, not_yet, other_ai)
   6. why: "What made you look for Projectify?" (several of: loses_track, agents_collide, team_cant_see, one_board, too_heavy, curious, other)
   7. current_tool: "What do you use today?" (one of: none, trello, jira, asana, linear, notion, monday, github, spreadsheets, other)
   8. source: "How did you hear about us?" (one of: search, ai, friend, social, newsletter, other)
   9. first_goal: "Is there a date or first milestone?" (an optional date YYYY-MM-DD and one line)
3. After each answer, call `act("save_onboarding", { path: "plugin", answers: { <key>: <value> } })` with just that answer (the option values above), so nothing is lost if we stop. On "Skip all", call it with skip_all: true and go to step 4.
4. Show me "Here is what we will make" in a few lines: the first project (a name, a 2–5 letter key and a template from mobile_app, website, saas, marketing, ecommerce, business, event, other; the Done by date) and its starter epic, the people step, the connect step. If I am not working alone, ask once for teammates' emails (optional). Ask ONE multiple-choice question: "Set it up like this?" with "Yes", "Change something" and "Not now". Change what I ask, never more.
5. On yes, call `act("apply_onboarding", { path: "plugin", timezone, project: { name, key, type }, repo_files })`: timezone is my IANA name (e.g. "Europe/London"; ask only if you do not know it), repo_files true when we are in a git repo in Claude Code. If I gave emails, call `act("invite_people", { people: [{ email, role: "member" }] })`.
6. Tell me what was made and the next steps, each in one line, as the replies give them. If the reply carries repo files, offer to write them into this repo (merge into what is there) and commit them; then suggest `/mcp__projectify__onboard_project <KEY>` to fill the Brief from the code.

Never create a project or invite anyone before my yes in step 4. If a tool says only owners can do something, stop and tell me. If a tool asks for a chat key, call start_session and pass its key.
