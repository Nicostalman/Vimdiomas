# M6 · Pinyin editable by hand — validation

The acceptance bar. Section numbers (§) refer to
[`requirements.md`](requirements.md).

## 1. Automated

- [ ] `uv run --extra dev pytest` passes in full.
- [ ] §6's tests 1–13 exist and pass: `normalise`'s table, refusals and round
      trip; `syllable_count`; Pinyin enabled, clickable and skipped by `tab`;
      `tab` from Pinyin goes to Translation; a hand edit survives a word
      change and gives way when emptied or when the form is cleared; Create
      stores the normalised hand edit; both refusals write nothing and keep
      the form; grammar paths behave the same; German is unchanged.
- [ ] The existing Entry and pinyin tests pass unchanged.

## 2. By the agent, in the real app

On a scratch Chinese notebook:

- [ ] Type 行 in Word: Pinyin shows the guess. Click Pinyin, type `xíng`,
      Create. The file holds `xing2`. Compile: the PDF prints `xíng`.
- [ ] Type 小/中/大號, click Pinyin, replace it with `xiǎo/zhōng/dàhào`,
      change the word to 小/中/大號碼: the hand edit stays. Create is refused
      (4 syllables, 5 hanzi). Fix the reading, Create: saved.
- [ ] `xyz3` → `"xyz3" isn't pinyin.`, nothing written, form kept.
- [ ] `tab` cycles Word → Translation → Note → Create → Word without
      stopping on Pinyin; `tab` in Pinyin goes to Translation.
- [ ] A German notebook's Entry: no Pinyin, `tab` order as before.

## 3. By hand (the dev)

- [ ] On a real Chinese notebook: fix a wrong guess with the mouse and Create.
      The PDF shows your reading.
- [ ] `tab` never lands on Pinyin.
- [ ] An unreadable reading and a wrong syllable count are both refused, with
      nothing added to the file.
- [ ] A German notebook's Entry looks and behaves as before.

## 4. Spec check

- [ ] `requirements.md`, `plan.md`, `design.md`, the roadmap and the code
      agree; anything that changed during implementation is recorded in
      `requirements.md` §7.
