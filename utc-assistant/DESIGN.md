# UTC Assistant Design System v2

## Visual Direction
- Operational dashboard for daily repeated use.
- Neutral slate-gray surfaces, high-contrast dark ink text.
- Blue primary (#2563eb), teal accent (#0d9488). Controlled, no gradients.
- Dense but scannable — card-based layouts with subtle borders and shadows.

## Design Tokens
- Source of truth: `design-tokens.json`.
- Token groups: color, typography, spacing, radius, shadow.

### Color Palette
| Role       | Value    | Usage                        |
|-----------|----------|------------------------------|
| bg        | #f8fafc  | App background               |
| surface   | #ffffff  | Cards, chat bubbles, forms   |
| surfaceHover | #f1f5f9 | Hover states              |
| text      | #0f172a  | Body text, headings          |
| textSecondary | #334155 | Secondary content       |
| textMuted | #64748b  | Captions, metadata           |
| border    | #e2e8f0  | Default borders              |
| borderStrong | #cbd5e1 | Form borders, emphasis    |
| primary   | #2563eb  | Buttons, links, active states|
| accent    | #0d9488  | Status badges, source headers|
| success   | #059669  | Success messages             |
| danger    | #dc2626  | Error states                 |

## Component Rules
- Panels/forms/tables/chat bubbles use white `surface` + `1px` `border`.
- Primary actions use `primary` blue fill; secondary remain white with hover blue accent.
- Caption/help text uses `textMuted`, minimum 12px.
- Header is an information bar (kicker + title + subtitle + status badge).
- Sidebar uses nav links styled as pills with icon prefixes.
- Chat workspace uses `chatBg`, `inputBg`, `send`, and `sendHover` tokens for the dedicated assistant experience.

### Chat
- Messages: white surface, border, subtle shadow, 8px radius.
- User messages: blue caption "Bạn", right-aligned feel.
- Assistant messages: teal caption "UTC Assistant · {model}", left-aligned.
- Source cards: expandable inline panels with score badges.
- Composer: bottom message bar with a soft input field and circular send action.
- History panel: real session-backed conversations only; no placeholder conversations that look like saved data.

### Navigation (Sidebar)
- Nav items with icon prefixes styled as pills.
- Active state: light blue background + blue border.
- Hover: light gray background.
- Footer: storage paths with folder icons.

## Accessibility Baseline
- Body text: #0f172a on #ffffff (contrast ratio > 15:1).
- Muted text: #64748b on #f8fafc (contrast ratio > 5:1).
- Focus states: blue ring `0 0 0 3px rgba(37,99,235,.15)` on all inputs.
- Interactive elements have visible hover and active states.

## Implementation Notes
- Next.js 15 App Router with shadcn/ui components and Tailwind CSS.
- Layout max-width: 1120px for readability.
- Sidebar and main content share the same token palette.
- Chat uses dedicated `chatBg`, `inputBg`, `send`, and `sendHover` tokens.
- Model badge shown on every assistant response.
- Source cards use expandable inline panels with score badges.
