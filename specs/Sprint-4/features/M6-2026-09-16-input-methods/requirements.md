# M6 · Input methods — requirements

Sprint 4, milestone 6. Branch `2026-09-16-m6-input-methods`.

The backlog's [*Instalation wizard*](../../guidelines/backlog.md) item 5, plus
`postponedfeatures.md`'s *Macism input fix*, which the dev brought in as its
consumer.

## The roadmap's anchor

Quoted from [`roadmap-sprint-4.md`](../../roadmap-sprint-4.md) · M6, which the
rest of this document elaborates on:

> **Deliverable.**
>
> - **A wizard step, after tree locations,** that asks for each chosen language:
>   for Chinese, the **hanzi** input method and the **translation** one; for
>   German, the **German** input method and the **translation** one. The two
>   answers may be the same.
> - The options come from the input sources **enabled on the machine**, listed
>   through the platform layer. If there's nothing suitable to pick, the user is
>   told to add an input source in System Settings.
> - **`input_method.py` reads the config.** Entry's hanzi field and the
>   translation-side switch use Chinese's configured sources instead of Sprint
>   2's hardcoded `SCIM.ITABC` / `USInternational-PC` pair. German's answers are
>   stored and unused while German is inert.
> - Everything Sprint 2 guaranteed still holds: a no-op off macOS, a no-op when
>   `macism` is missing, and the switch runs in a worker thread.
>
> **Done when.** The wizard lists the dev's real enabled input sources; the
> choices are saved; Entry's hanzi field switches to the chosen hanzi source and
> back to the chosen translation source; changing those sources in the config
> changes what Entry switches to, with no code edit; and the full test suite
> passes.

## What the spec conversation settled

The roadmap left three questions open. All three were answered by the dev on
2026-09-18, and the third answer **widened the milestone** beyond the roadmap's
own deliverable — see *Scope added by the dev*, below.

### 1. Mapping `defaults` entries to `macism` IDs

Resolved by inspection on the dev's machine rather than by asking. The notes'
Assumption — that the IDs don't match one-to-one — holds, and the mapping is
mechanical:

`defaults export com.apple.HIToolbox -` returns an **XML plist** (unlike
`defaults read`'s NeXTSTEP format, which has no parser in the standard
library), so `plistlib` reads it directly with no dependency added. Its
`AppleEnabledInputSources` array holds one dict per enabled source, keyed by
`InputSourceKind`:

| `InputSourceKind` | macism ID | Example |
| --- | --- | --- |
| `Keyboard Layout` | `com.apple.keylayout.` + `KeyboardLayout Name` | `com.apple.keylayout.USInternational-PC` |
| `Input Mode` | the `Input Mode` value, already a full ID | `com.apple.inputmethod.SCIM.ITABC` |
| `Keyboard Input Method` | the `Bundle ID`, **only when** no `Input Mode` entry shares that bundle | — |
| `Non Keyboard Input Method` | *skipped* | Character palette, Press-and-Hold, emoji |

The `Keyboard Input Method` rule exists because a multi-mode IME appears twice:
once as the container (`com.apple.inputmethod.SCIM`) and once per mode
(`…SCIM.ITABC`). Offering the container alongside its own modes would be a
duplicate that switches to an arbitrary one. An IME with no modes at all still
needs its container listed, which is what the "only when" clause preserves.

Verified against the dev's machine: six enabled entries reduce to exactly two
selectable sources — `com.apple.keylayout.USInternational-PC` and
`com.apple.inputmethod.SCIM.ITABC` — the same pair Sprint 2 hardcoded, and
`macism` with no arguments confirms it accepts and reports the first verbatim.

### 2. What "translation" means on the German side

**Kept generic.** The two fields are labelled *"Chinese input"* / *"German
input"* and *"Translation input"*. The dev's first phrasing named the second
field "English input"; asked directly, they chose not to commit the UI to
English being the translation language. Stored as `input_method` and
`translation_input_method` — see *Config schema*, below.

### 3. An empty or insufficient list

**Never blocking.** The dev's own words:

> for example in chinese, if theres only the english keyboard, ask the user to
> add a chinese keyboard and to change it later […] then […] both the english
> and chinese input use the available keyboard (in this case english). this
> means the user wont be able to input chinese characters and the input wont
> switch. when he realises this, he will go to settings and add the input
> method manually.

So: with one source, both fields preselect it and the step warns; with none, the
step says to add one in System Settings and still lets the wizard finish. Input
switching degrades to a no-op, exactly as it already does without `macism`. The
wizard never refuses to complete over an input method.

## Scope added by the dev

Asked whether "settings" meant the wizard's own fields or a real Settings
screen — the Settings submenu being all-dummy and postponed by this sprint's
notes — the dev chose **a real Settings screen now**. That is a deliberate
widening of M6 past the roadmap's deliverable, taken on the dev's explicit call,
and it is what answers their follow-up worry:

> if no input method is stored in hanzi, then how would the user be able to use
> the app? its obvious, it should have a default setting

Two things answer it together:

1. **The wizard always stores a concrete ID when the machine has any source at
   all.** An empty stored value is only reachable with *zero* enabled sources —
   where there is, by definition, nothing to switch to — or in a hand-written
   config. In both cases the switch no-ops and the user simply types with
   whatever keyboard they have. Nothing breaks and no screen is unusable.
2. **Settings gives an in-app fix path**, so realising the choice was wrong no
   longer means hand-editing `~/.config/idiomas/config.toml`.

The widening is **narrow**: Settings gains input methods and nothing else. *Add
a language* and *Remove a notebook* stay dummy placeholders, and the Settings
submenu as a whole stays postponed to a later sprint.

## Scope

### In

1. **Platform-layer source listing.** `idiomas.platform.list_input_sources()`
   returns the machine's enabled, switchable sources as `InputSource(id, name)`
   values, newest layer of the same platform boundary M4 built. macOS
   implements it per the mapping table above; every other platform returns `[]`,
   matching the layer's existing inert-no-op rule.
2. **A `SelectField` widget** in `panels.py`: a focusable field showing the
   current choice, which expands a `VimOptionList` on `enter` and collapses on
   `esc` or on choosing. It is the dev's described UI ("inside each field a list
   will deploy with all available input methods") and it nests exactly the way
   `design.md`'s model already expects — content → field → panel → backpanel.
3. **A wizard step per registered language**, pushed after tree location, in the
   order the languages were chosen. Two `SelectField`s and a `Next`/`Finish`
   button. The last one writes the config.
4. **Settings → Input methods**, a real screen: a menu of the registered
   languages, then the same two fields prefilled from the config, and `Save`,
   which rewrites the config atomically and updates the running app in place.
5. **`input_method.py` reads the config.** The hardcoded `SCIM.ITABC` /
   `USInternational-PC` constants go away. `NotebookConfig` carries the two IDs
   down to Entry's `HanziInput`.
6. **Config field rename:** `hanzi_input_method` → `input_method`. The dev's
   hand-written `~/.config/idiomas/config.toml` is updated as part of the
   milestone.
7. `design.md` records the `SelectField` convention and the Settings surface;
   `stack.md` records the platform-layer addition and the config schema change.

### Out

- **Any other Settings item.** *Add a language* and *Remove a notebook* stay
  placeholders.
- **A working German notebook.** German's answers are stored and unused, as the
  roadmap says.
- **Installing or enabling an input source for the user.** The app reads what
  macOS reports and points at System Settings; it never writes there.
- **Localised source names from the Carbon `TIS` API.** That needs `pyobjc`, a
  dependency this project doesn't have and doesn't want for cosmetics. Names
  come from a small table of common sources with the raw ID as the fallback, and
  every option shows its ID alongside the name regardless.
- **Migrating the old hardcoded pair into anyone's config.** The dev reruns the
  wizard or uses Settings.

## Config schema

`LanguageConfig` after this milestone:

```toml
[[languages]]
name = 'Chinese'
input_method = 'com.apple.inputmethod.SCIM.ITABC'
translation_input_method = 'com.apple.keylayout.USInternational-PC'
```

`input_method` is the language's own script/IME; `translation_input_method` is
what the user types translations with. Both default to `""` when absent, which
means "don't switch". `hanzi_input_method` is **not** read as a fallback — no
config outside the dev's own machine has ever contained it, and M4's standing
decision is that old config keys are ignored, not migrated.

## Preselection

Every list is unfiltered — the dev's call: all enabled keyboard sources appear
in both fields, since a heuristic that hides a valid choice is worse than one
that merely orders badly. Preselection *is* a heuristic, and only chooses which
option starts highlighted:

- An already-configured value always wins (Settings, and a wizard step revisited
  with `q`).
- Otherwise the language field takes the first source whose ID matches that
  language's hints (Chinese: `SCIM`, `TCIM`, `Pinyin`, `Zhuyin`, `Cangjie`,
  `Wubi`; German: `German`), falling back to the first source.
- Otherwise the translation field takes the first `com.apple.keylayout.*` source
  that the language field didn't take, falling back to the first source.
- With exactly one source, both fields land on it — the dev's stated case.

## Context

- **Sprint 2 M4** built the switching itself
  (`specs/Sprint-2/features/2026-09-07-m4-macos-input-method-switching/`). Its
  three guarantees are load-bearing and unchanged here: a no-op off macOS, a
  no-op when `macism` is missing or the source is unavailable, and the switch
  running in a worker thread owned by `self.app`. `HanziInput`'s
  `from_app_focus` / `app_focus` guards against macism's own focus blip are
  untouched.
- **Sprint 4 M4** built `idiomas.platform` and the config; **M5** built the
  wizard and `save_config`'s atomic temp-file + `os.replace` write. This
  milestone adds to both rather than reworking either.
- **Sprint 4 M1/M2** built `Panel`/`Backpanel`/`TextField`. `SelectField` joins
  them in `panels.py` and follows the same `SkipAction`-guarded bubbling rules.
