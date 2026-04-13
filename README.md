# Instant Jokes — Home Assistant Integration

<p align="center">
  <img src="images/logo.png" alt="bdihot.co.il" width="280"/>
</p>

<p align="center">
  <a href="https://github.com/hacs/integration"><img src="https://img.shields.io/badge/HACS-Custom-orange.svg" alt="HACS"></a>
  <a href="https://github.com/Guy008/joke/releases"><img src="https://img.shields.io/github/v/release/Guy008/joke" alt="Release"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="License"></a>
  <img src="https://img.shields.io/badge/HA-2024.1%2B-brightgreen" alt="HA Version">
</p>

---

> 🇬🇧 [English](#english) | 🇮🇱 [עברית](#עברית)

---

## English

### Overview

**Instant Jokes** is a Home Assistant custom integration that fetches Hebrew jokes from [bdihot.co.il](https://www.bdihot.co.il) and exposes them as a sensor entity.

The integration maintains a queue of three jokes at all times. The current joke is the sensor state; the next two are available as attributes. Services allow advancing the queue or refreshing it on demand — making it ideal for voice assistants, automations, and dashboards.

The UI language adapts to your Home Assistant language setting. Currently supported: **English**, **Hebrew**.

---

### Requirements

- Home Assistant **2024.1.0** or newer
- [HACS](https://hacs.xyz) for easy installation (or manual install)

---

### Installation

#### Via HACS (recommended)

> New to HACS? See the [HACS documentation](https://hacs.xyz/docs/use/).

1. In Home Assistant, open **HACS → Integrations**
2. Click **⋮** → **Custom repositories**
3. Enter `https://github.com/Guy008/joke` and set the category to **Integration**
4. Click **Add**, then search for **Instant Jokes** and click **Download**
5. Restart Home Assistant
6. Go to **Settings → Devices & Services → Add Integration**
7. Search for **Instant Jokes** and click **Submit**

#### Manual Installation

1. Download the latest release from the [Releases page](https://github.com/Guy008/joke/releases)
2. Extract the archive
3. Copy the `custom_components/jokes_il/` folder into your Home Assistant `config/custom_components/` directory:

```
config/
└── custom_components/
    └── jokes_il/
        ├── __init__.py
        ├── config_flow.py
        ├── coordinator.py
        ├── sensor.py
        ├── manifest.json
        └── ...
```

4. Restart Home Assistant
5. Go to **Settings → Devices & Services → Add Integration**
6. Search for **Instant Jokes** and click **Submit**

---

### Sensor Reference

After setup, the following entity is created:

**`sensor.instant_jokes`**

| Field | Type | Description |
|-------|------|-------------|
| state | `string` | Body text of the current joke |
| `title` | `string` | Title of the current joke |
| `joke_2` | `string` | Body text of the next joke in queue |
| `title_2` | `string` | Title of the next joke |
| `joke_3` | `string` | Body text of the third joke in queue |
| `title_3` | `string` | Title of the third joke |
| `type` | `string` | Category: `clean`, `adult`, `ethnic`, or `unknown` |
| `safe` | `boolean` | `true` only when `type` is `clean` |
| `url` | `string` | Source URL of the current joke on bdihot.co.il |

---

### Services Reference

#### `jokes_il.next_joke`

Advances the queue. `joke_2` becomes the current joke, `joke_3` becomes `joke_2`.

```yaml
action: jokes_il.next_joke
```

#### `jokes_il.refresh_jokes`

Discards the current queue and fetches a fresh batch of jokes from the API immediately, without waiting for the next scheduled update.

```yaml
action: jokes_il.refresh_jokes
```

> The integration auto-refreshes every **6 hours**. Use `refresh_jokes` only when you need an immediate update.

---

### Verifying the Installation

1. Go to **Developer Tools → States**
2. Search for `sensor.instant_jokes`
3. Confirm the state contains joke text and the attributes include `title`, `joke_2`, `type`, and `safe`

---

### Automations

#### Voice Assistant — Automatic Queue Advancement

This is the primary use case. When a user asks for a joke, the assistant reads the current joke and the queue advances automatically, so the next request always gets a different joke.

**How it works:** `set_conversation_response` captures the current joke before `jokes_il.next_joke` runs. Since HA sends the conversation response at the end of the action sequence, the correct joke is always read aloud even though the queue advances within the same run.

```yaml
alias: Joke request
description: >
  Responds to voice requests for a joke and automatically advances the
  queue so the next request gets a different joke.
triggers:
  - trigger: conversation
    command:
      - tell me a joke
      - joke
      - another joke
      - ספר לי בדיחה
      - ספר בדיחה
      - עוד בדיחה
      - בדיחה
conditions: []
actions:
  - set_conversation_response: "{{ states('sensor.instant_jokes') }}"
  - action: jokes_il.next_joke
mode: single
```

> **Important:** Do not use `parallel` here. The response must be captured in the first step before the queue advances.

---

#### Morning Notification

Send a joke to your phone every morning, including the title as the notification heading.

```yaml
alias: Morning joke
description: Sends a joke notification every morning and advances the queue.
triggers:
  - trigger: time
    at: "08:00:00"
conditions: []
actions:
  - action: notify.mobile_app_your_phone
    data:
      title: "{{ state_attr('sensor.instant_jokes', 'title') }}"
      message: "{{ states('sensor.instant_jokes') }}"
  - action: jokes_il.next_joke
mode: single
```

Replace `notify.mobile_app_your_phone` with your actual notification service entity.

---

#### Safe Content Filter

Only respond when the joke is classified as clean. Useful for shared screens, children's rooms, or family-friendly voice assistants.

```yaml
alias: Safe joke only
description: >
  Responds to joke requests only when the current joke is classified
  as clean by bdihot.co.il.
triggers:
  - trigger: conversation
    command:
      - tell me a joke
      - joke
      - ספר לי בדיחה
      - בדיחה
conditions:
  - condition: template
    value_template: "{{ state_attr('sensor.instant_jokes', 'safe') == true }}"
actions:
  - set_conversation_response: "{{ states('sensor.instant_jokes') }}"
  - action: jokes_il.next_joke
mode: single
```

> If the current joke is not clean, the automation does not respond. You can add a fallback action (e.g., call `jokes_il.next_joke` silently) to advance past non-clean jokes automatically.

---

#### Skip Non-Clean Jokes Automatically

Extend the safe filter to silently skip non-clean jokes until a clean one is found.

```yaml
alias: Safe joke — skip non-clean
description: >
  When a joke is requested, skip non-clean jokes until a clean one is
  available, then respond.
triggers:
  - trigger: conversation
    command:
      - tell me a joke
      - joke
      - ספר לי בדיחה
      - בדיחה
conditions: []
actions:
  - repeat:
      while:
        - condition: template
          value_template: "{{ state_attr('sensor.instant_jokes', 'safe') != true }}"
      sequence:
        - action: jokes_il.next_joke
        - delay:
            milliseconds: 200
  - set_conversation_response: "{{ states('sensor.instant_jokes') }}"
  - action: jokes_il.next_joke
mode: single
```

---

#### Lovelace Dashboard Card

Display the current joke on a dashboard. Tapping the card advances to the next joke.

```yaml
type: markdown
tap_action:
  action: perform-action
  perform_action: jokes_il.next_joke
entities:
  - sensor.instant_jokes
content: |
  {{ state_attr('sensor.instant_jokes', 'title') }}

  {{ states('sensor.instant_jokes') }}
text_only: true
grid_options:
  columns: full
```

**Optional styling** — requires the [card-mod](https://github.com/thomasloven/lovelace-card-mod) HACS frontend card:

```yaml
type: markdown
tap_action:
  action: perform-action
  perform_action: jokes_il.next_joke
entities:
  - sensor.instant_jokes
content: |
  {{ state_attr('sensor.instant_jokes', 'title') }}

  {{ states('sensor.instant_jokes') }}
text_only: true
grid_options:
  columns: full
card_mod:
  style: |
    ha-card {
      background: none !important;
      box-shadow: none !important;
      border: none !important;
      width: 100%;
      font-size: 2rem !important;
      font-weight: bold;
      color: #03ff90 !important;
      -webkit-text-stroke: 1px black;
    }
```

> Tap the card to advance to the next joke. To display all three queued jokes, duplicate the card and replace `states(...)` with `state_attr('sensor.instant_jokes', 'joke_2')`.

---

### Troubleshooting

| Symptom | Resolution |
|---------|------------|
| Integration not found after installation | Restart Home Assistant, then retry |
| Sensor state is empty or `אין בדיחה` | The API did not respond. Call `jokes_il.refresh_jokes` to retry |
| Jokes are repeating | The deduplication memory holds 20 entries. With very frequent use the pool may cycle. This is expected |
| Errors in logs | Go to **Settings → System → Logs** and filter for `jokes_il` |

---

### Data Source

All content is fetched from [bdihot.co.il](https://www.bdihot.co.il) via their public JSON API. This integration does not store, cache beyond the runtime session, or redistribute joke content.

---

---

## עברית

### סקירה

**Instant Jokes** היא אינטגרציה מותאמת אישית ל-Home Assistant שמושכת בדיחות עבריות מ-[bdihot.co.il](https://www.bdihot.co.il) ומציגה אותן כישות sensor.

האינטגרציה מנהלת תור של שלוש בדיחות בכל עת. הבדיחה הנוכחית היא ה-state של החיישן; השתיים הבאות זמינות כ-attributes. שירותים מאפשרים להתקדם בתור או לרענן אותו לפי דרישה — מה שהופך את האינטגרציה למתאימה במיוחד לעוזרים קוליים, אוטומציות ודשבורדים.

שפת הממשק מסתגלת לשפת ה-Home Assistant שלך. נתמכות כרגע: **עברית**, **אנגלית**.

---

### דרישות

- Home Assistant גרסה **2024.1.0** ומעלה
- [HACS](https://hacs.xyz) להתקנה נוחה (או התקנה ידנית)

---

### התקנה

#### דרך HACS (מומלץ)

> חדש ב-HACS? ראה את [תיעוד HACS](https://hacs.xyz/docs/use/).

1. פתח **HACS → Integrations**
2. לחץ **⋮** → **Custom repositories**
3. הכנס `https://github.com/Guy008/joke` ובחר קטגוריה **Integration**
4. לחץ **Add**, חפש **Instant Jokes** ולחץ **Download**
5. הפעל מחדש את Home Assistant
6. לך ל־ **Settings → Devices & Services → Add Integration**
7. חפש **Instant Jokes** ולחץ **Submit**

#### התקנה ידנית

1. הורד את הגרסה האחרונה מעמוד [Releases](https://github.com/Guy008/joke/releases)
2. פתח את הארכיון
3. העתק את התיקייה `custom_components/jokes_il/` לתוך `config/custom_components/` שלך:

```
config/
└── custom_components/
    └── jokes_il/
        ├── __init__.py
        ├── config_flow.py
        ├── coordinator.py
        ├── sensor.py
        ├── manifest.json
        └── ...
```

4. הפעל מחדש את Home Assistant
5. לך ל־ **Settings → Devices & Services → Add Integration**
6. חפש **Instant Jokes** ולחץ **Submit**

---

### מידע על החיישן

לאחר ההגדרה, נוצרת ישות:

**`sensor.instant_jokes`**

| שדה | סוג | תיאור |
|-----|-----|-------|
| state | `string` | גוף הבדיחה הנוכחית |
| `title` | `string` | כותרת הבדיחה הנוכחית |
| `joke_2` | `string` | גוף הבדיחה הבאה בתור |
| `title_2` | `string` | כותרת הבדיחה הבאה |
| `joke_3` | `string` | גוף הבדיחה השלישית בתור |
| `title_3` | `string` | כותרת הבדיחה השלישית |
| `type` | `string` | קטגוריה: `clean`, `adult`, `ethnic`, או `unknown` |
| `safe` | `boolean` | `true` רק כאשר `type` הוא `clean` |
| `url` | `string` | כתובת המקור של הבדיחה ב-bdihot.co.il |

---

### מידע על השירותים

#### `jokes_il.next_joke`

מתקדם בתור. `joke_2` הופכת לנוכחית, `joke_3` הופכת ל-`joke_2`.

```yaml
action: jokes_il.next_joke
```

#### `jokes_il.refresh_jokes`

מוחק את התור הנוכחי ומוריד סט חדש של בדיחות מה-API מיד, ללא המתנה לרענון המתוזמן.

```yaml
action: jokes_il.refresh_jokes
```

> האינטגרציה מתרעננת אוטומטית כל **6 שעות**. השתמש ב-`refresh_jokes` רק כשצריך עדכון מיידי.

---

### בדיקת ההתקנה

1. לך ל־ **Developer Tools → States**
2. חפש `sensor.instant_jokes`
3. וודא שה-state מכיל טקסט בדיחה וה-attributes כוללים `title`, `joke_2`, `type`, ו-`safe`

---

### אוטומציות

#### עוזר קולי — התקדמות תור אוטומטית

זה המקרה השימושי המרכזי. כשמשתמש מבקש בדיחה, העוזר מקריא את הבדיחה הנוכחית והתור מתקדם אוטומטית, כך שהבקשה הבאה תמיד מקבלת בדיחה אחרת.

**איך זה עובד:** `set_conversation_response` לוכד את הבדיחה הנוכחית לפני ש-`jokes_il.next_joke` רץ. מכיוון ש-HA שולח את תגובת השיחה בסוף רצף הפעולות, הבדיחה הנכונה תמיד מוקראת גם כשהתור מתקדם באותה ריצה.

```yaml
alias: בקשת בדיחה
description: >
  מגיב לבקשות קוליות לבדיחה ומתקדם אוטומטית בתור
  כך שהבקשה הבאה תקבל בדיחה שונה.
triggers:
  - trigger: conversation
    command:
      - ספר לי בדיחה
      - ספר בדיחה
      - עוד בדיחה
      - בדיחה
      - tell me a joke
      - joke
conditions: []
actions:
  - set_conversation_response: "{{ states('sensor.instant_jokes') }}"
  - action: jokes_il.next_joke
mode: single
```

> **חשוב:** אל תשתמש ב-`parallel`. התגובה חייבת להילכד בשלב הראשון לפני שהתור מתקדם.

---

#### התראת בוקר

שליחת בדיחה לטלפון כל בוקר, כולל הכותרת כנושא ההתראה.

```yaml
alias: בדיחת בוקר
description: שולח בדיחה כל בוקר ומתקדם בתור.
triggers:
  - trigger: time
    at: "08:00:00"
conditions: []
actions:
  - action: notify.mobile_app_your_phone
    data:
      title: "{{ state_attr('sensor.instant_jokes', 'title') }}"
      message: "{{ states('sensor.instant_jokes') }}"
  - action: jokes_il.next_joke
mode: single
```

החלף `notify.mobile_app_your_phone` בשירות ההתראות בפועל שלך.

---

#### סינון תוכן בטוח

תגובה רק כשהבדיחה מסווגת כנקייה. שימושי למסכים משותפים, חדרי ילדים, או עוזרים קוליים ידידותיים למשפחה.

```yaml
alias: בדיחה בטוחה בלבד
description: >
  מגיב לבקשות בדיחה רק כשהבדיחה הנוכחית מסווגת
  כנקייה על ידי bdihot.co.il.
triggers:
  - trigger: conversation
    command:
      - ספר לי בדיחה
      - בדיחה
      - joke
conditions:
  - condition: template
    value_template: "{{ state_attr('sensor.instant_jokes', 'safe') == true }}"
actions:
  - set_conversation_response: "{{ states('sensor.instant_jokes') }}"
  - action: jokes_il.next_joke
mode: single
```

---

#### דילוג אוטומטי על בדיחות לא נקיות

הרחב את הסינון כך שידלג בשקט על בדיחות לא נקיות עד שתמצא נקייה.

```yaml
alias: בדיחה בטוחה — דילוג על לא נקיות
description: >
  כשמבקשים בדיחה, מדלג על בדיחות לא נקיות עד שמוצאת נקייה,
  ואז מגיב.
triggers:
  - trigger: conversation
    command:
      - ספר לי בדיחה
      - בדיחה
      - joke
conditions: []
actions:
  - repeat:
      while:
        - condition: template
          value_template: "{{ state_attr('sensor.instant_jokes', 'safe') != true }}"
      sequence:
        - action: jokes_il.next_joke
        - delay:
            milliseconds: 200
  - set_conversation_response: "{{ states('sensor.instant_jokes') }}"
  - action: jokes_il.next_joke
mode: single
```

---

#### כרטיס דשבורד (Lovelace)

הצגת הבדיחה הנוכחית על הדשבורד. לחיצה על הכרטיס מתקדמת לבדיחה הבאה.

```yaml
type: markdown
tap_action:
  action: perform-action
  perform_action: jokes_il.next_joke
entities:
  - sensor.instant_jokes
content: |
  {{ state_attr('sensor.instant_jokes', 'title') }}

  {{ states('sensor.instant_jokes') }}
text_only: true
grid_options:
  columns: full
```

**עיצוב מתקדם** — דורש את כרטיס [card-mod](https://github.com/thomasloven/lovelace-card-mod) מ-HACS:

```yaml
type: markdown
tap_action:
  action: perform-action
  perform_action: jokes_il.next_joke
entities:
  - sensor.instant_jokes
content: |
  {{ state_attr('sensor.instant_jokes', 'title') }}

  {{ states('sensor.instant_jokes') }}
text_only: true
grid_options:
  columns: full
card_mod:
  style: |
    ha-card {
      background: none !important;
      box-shadow: none !important;
      border: none !important;
      width: 100%;
      font-size: 2rem !important;
      font-weight: bold;
      color: #03ff90 !important;
      -webkit-text-stroke: 1px black;
    }
```

> לחיצה על הכרטיס מתקדמת לבדיחה הבאה. להצגת שלוש בדיחות בו-זמנית, שכפל את הכרטיס והחלף `states(...)` ב-`state_attr('sensor.instant_jokes', 'joke_2')`.

---

### פתרון תקלות

| תסמין | פתרון |
|-------|-------|
| Integration לא מופיע לאחר ההתקנה | הפעל מחדש את Home Assistant ונסה שוב |
| ה-state ריק או מציג `אין בדיחה` | ה-API לא הגיב. קרא ל-`jokes_il.refresh_jokes` לנסות שוב |
| בדיחות חוזרות על עצמן | זיכרון הכפילויות מכיל 20 ערכים. בשימוש תכוף מאוד הבריכה עשויה להתחזר — זה צפוי |
| שגיאות ב-Logs | לך ל- **Settings → System → Logs** וסנן לפי `jokes_il` |

---

### מקור הנתונים

כל התוכן נשלף מ-[bdihot.co.il](https://www.bdihot.co.il) דרך ה-API הציבורי שלהם. האינטגרציה לא שומרת, לא מאחסנת מעבר לסשן הריצה, ולא מפיצה תוכן בדיחות.

---

## Credits

| Role | Credit |
|------|--------|
| Concept & Direction | [Guy Levy](https://github.com/Guy008) |
| Architecture & Implementation | [Claude Sonnet 4.6](https://www.anthropic.com/claude) by [Anthropic](https://www.anthropic.com) |
| Joke Content | [bdihot.co.il](https://www.bdihot.co.il) |

---

## License

[MIT](LICENSE) © 2026 Guy Levy
