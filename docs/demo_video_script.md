# NetSage AI — Demo Video Script (5–10 minutes)

I can't record video for you, but here's a ready-to-follow script/storyboard
that hits every point the "How Your Work Will Be Checked" table looks for.
Record your screen (OBS, Loom, or PowerPoint's built-in recorder) while
following these beats. Suggested total: ~8 minutes.

## Segment 1 — Introduce the broken lab (0:00–1:30)
- Open Packet Tracer with a lab you've deliberately broken, e.g. **C007
  (gateway mismatch)**: PC1 configured with the wrong default gateway.
- Show the symptom on screen: `ping` from PC1 to a remote server times out.
- Say what a junior engineer would see: "IP looks fine, ping to the local
  subnet works, but nothing beyond it responds."

## Segment 2 — Collect evidence (1:30–2:30)
- Run `ipconfig` on PC1, `show ip interface brief` on R1.
- Point out the two numbers on screen that should match and don't.

## Segment 3 — Run the AI diagnosis (2:30–4:30)
- Open `prompts/diagnose_prompt.md`, briefly show the system prompt.
- Paste the case's symptom/topology/show-output into your AI assistant
  (or show `logs/ai_diagnosis.csv` row for C007 already computed).
- Read the returned JSON aloud: root_cause, osi_layer, confidence,
  evidence, next_command, fix_steps.
- Emphasize: **the AI has not touched the router or PC — it only
  recommended.**

## Segment 4 — Human review (4:30–6:00)
- Open `logs/human_review_log.csv`, find case C007 → status "Accepted".
- Also show one **corrected** case from `logs/responsible_ai_log.md`
  (e.g. C019 or C026) side by side, explaining in your own words why the
  human reviewer overrode the AI. This is the safety-rule moment — call
  it out explicitly on camera.

## Segment 5 — Apply the fix and verify (6:00–7:30)
- Back in Packet Tracer, apply the approved fix_steps for C007
  (set PC1's gateway to 192.168.1.1).
- Re-run the `ping` to prove the fix worked.
- Run `scripts/rule_checker.py` on screen and show the deterministic
  checker also flags/clears the same issue independently of the AI.

## Segment 6 — Wrap-up with the dashboard (7:30–8:30)
- Open `dashboard/dashboard.xlsx`, walk through the two charts:
  issue-type counts and human review outcomes.
- State the headline numbers out loud: 36 cases, 75% AI/human agreement
  rate, 10 cases the human reviewer corrected.
- Close with the one-sentence takeaway: "The AI speeds up the first
  guess; the human still owns every fix."

## Recording checklist
- [ ] Screen resolution readable at 1080p
- [ ] Mic audio clear, no background noise
- [ ] Every file referenced above is on screen at least once
- [ ] Video is 5–10 minutes
- [ ] Export as .mp4 and name it `netsage_demo.mp4`
