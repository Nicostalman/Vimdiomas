# M6 · Pinyin editable by hand — validation

The acceptance bar. Section numbers (§) refer to
[`requirements.md`](requirements.md).

## 1. Automated

- [x] `uv run --extra dev pytest` passes in full.
- [x] §6's tests 1–13 exist and pass: `normalise`'s table, refusals and round
      trip; `syllable_count`; Pinyin enabled, clickable and skipped by `tab`;
      `tab` from Pinyin goes to Translation; a hand edit survives a word
      change and gives way when emptied or when the form is cleared; Create
      stores the normalised hand edit; both refusals write nothing and keep
      the form; grammar paths behave the same; German is unchanged.
- [x] The existing Entry and pinyin tests pass unchanged, except the one that
      asserted the field was disabled (`requirements.md` §7).

## 2. By the agent, in the real app

On a scratch Chinese notebook:

- [x] Type 行 in Word: Pinyin shows the guess. Click Pinyin, type `xíng`,
      Create. The file holds `xing2`. Compile: the PDF prints `xíng`.
- [x] Type 小/中/大號, click Pinyin, replace it with `xiǎo/zhōng/dàhào`,
      change the word to 小/中/大號碼: the hand edit stays. Create is refused
      (4 syllables, 5 hanzi). Fix the reading, Create: saved.
- [x] `xyz3` → `"xyz3" isn't pinyin.`, nothing written, form kept.
- [x] `tab` cycles Word → Translation → Note → Create → Word without
      stopping on Pinyin; `tab` in Pinyin goes to Translation.
- [x] A German notebook's Entry: no Pinyin, `tab` order as before.

Seen on 2026-11-08, the real CLI in tmux with a scratch `HOME`, clicks sent as
mouse events: every line above behaved as written. `行` with `xíng` was stored
as `xing2`, and leaving Entry compiled a PDF printing `xíng`. The saved
小/中/大號碼 printed `xiǎo/zhōng/dàhàomǎ`.

## 3. By hand (the dev)

- [ ] On a real Chinese notebook: fix a wrong guess with the mouse and Create.
      The PDF shows your reading.
- [ ] `tab` never lands on Pinyin.
- [ ] An unreadable reading and a wrong syllable count are both refused, with
      nothing added to the file.
- [ ] A German notebook's Entry looks and behaves as before.

## 4. Spec check

- [x] `requirements.md`, `plan.md`, `design.md`, the roadmap and the code
      agree; anything that changed during implementation is recorded in
      `requirements.md` §7.
