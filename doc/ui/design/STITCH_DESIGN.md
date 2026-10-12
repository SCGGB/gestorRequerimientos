---
name: Institutional Spec Engine
colors:
  surface: '#f8f9ff'
  surface-dim: '#ccdbf4'
  surface-bright: '#f8f9ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#eff4ff'
  surface-container: '#e6eeff'
  surface-container-high: '#dde9ff'
  surface-container-highest: '#d5e3fd'
  on-surface: '#0d1c2f'
  on-surface-variant: '#42474f'
  inverse-surface: '#233144'
  inverse-on-surface: '#ebf1ff'
  outline: '#727780'
  outline-variant: '#c2c7d1'
  surface-tint: '#2d6197'
  primary: '#00355f'
  on-primary: '#ffffff'
  primary-container: '#0f4c81'
  on-primary-container: '#8ebdf9'
  inverse-primary: '#a0c9ff'
  secondary: '#545f73'
  on-secondary: '#ffffff'
  secondary-container: '#d5e0f8'
  on-secondary-container: '#586377'
  tertiary: '#003756'
  on-tertiary: '#ffffff'
  tertiary-container: '#004e78'
  on-tertiary-container: '#74c1ff'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#d2e4ff'
  primary-fixed-dim: '#a0c9ff'
  on-primary-fixed: '#001c37'
  on-primary-fixed-variant: '#07497d'
  secondary-fixed: '#d8e3fb'
  secondary-fixed-dim: '#bcc7de'
  on-secondary-fixed: '#111c2d'
  on-secondary-fixed-variant: '#3c475a'
  tertiary-fixed: '#cce5ff'
  tertiary-fixed-dim: '#93ccff'
  on-tertiary-fixed: '#001d31'
  on-tertiary-fixed-variant: '#004b73'
  background: '#f8f9ff'
  on-background: '#0d1c2f'
  surface-variant: '#d5e3fd'
typography:
  display-hero:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
  headline-lg:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  headline-md:
    fontFamily: Inter
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
  headline-sm:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '600'
    lineHeight: 24px
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  body-sm:
    fontFamily: Inter
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 18px
  label-md:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.025em
  label-micro:
    fontFamily: Inter
    fontSize: 11px
    fontWeight: '700'
    lineHeight: 14px
    letterSpacing: 0.05em
  code-snippet:
    fontFamily: JetBrains Mono
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 16px
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  gutter: 1.5rem
  gutter-sm: 0.75rem
  margin: 2rem
  margin-mobile: 1rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 1rem
  space-lg: 1.5rem
  space-xl: 2rem
---

## Brand & Style

The design system is engineered for enterprise-grade, institutional precision. It serves business analysts, software architects, compliance officers, and public or corporate administrators tasked with compiling mission-critical Software Requirements Specifications (SRS / ERS). 

The emotional tone balances rigorous governance with friction-free operational efficiency. The user experience must project stability, meticulous validation, clarity, and authoritative structure. Visual aesthetics draw from **Corporate / Modern** utilitarian design systems, rejecting decorative excess in favor of structured data density, unambiguous status communication, and high-trust institutional professionalism.

## Colors

The system relies on an institutional palette configured for compliance, clarity, and sustained focus:

- **Primary (`#0f4c81`)**: Deep Classic Institutional Blue for core actions, persistent navigation anchors, step highlights, and structural emphasis.
- **Secondary / Dark Neutral (`#1e293b`)**: Midnight Slate for high-emphasis typography, primary table headers, and structural dividers.
- **Tertiary / Info (`#0284c7`)**: Sky Blue reserved for intelligent assistants, auto-completion badges, and instructional helper elements.
- **Neutral Dark (`#334155`)**: Slate for standard body copy, field labels, and secondary actions.
- **Canvas & Surface**: 
  - Background Canvas: Slate 50 (`#f8fafc`) to minimize glare during prolonged drafting sessions.
  - Card & Container Surface: Crisp Pure White (`#ffffff`) framed with Slate 200 (`#e2e8f0`) perimeter borders.
  - Active / Muted Tints: Slate 100 (`#f1f5f9`) for table headers, disabled form controls, and static input group addons.
- **Functional Semantics**:
  - Success (`#10b981`): Certified validation pass, finalized sections, and completed status tokens.
  - Warning (`#d97706`): Incomplete drafts, non-blocking validation notices, and review flags.
  - Danger (`#dc3545`): Unmet requirement criteria, critical syntax/SRS errors, and hard blockers.

## Typography

Typography is centered on **Inter** (with native system fallbacks: `-apple-system`, `BlinkMacSystemFont`, `Segoe UI`, `Roboto`, `Helvetica Neue`, `sans-serif`) to ensure maximum screen rendering speed and legibility across government and enterprise equipment.

- **Micro-labels (`label-micro`)**: Always rendered in uppercase with subtle letter-spacing for document identifiers (e.g., `RF-001`, `CASO DE USO`, `REVISION`), status tags, and table column heads.
- **Form Labels**: Standardized at `body-md` (14px) with bold weight (`600`) and explicit required indicators using high-visibility Crimson (`#dc3545`).
- **Data Tables & Forms**: Default to `body-md` (14px) and `body-sm` (13px) to maximize data density while preserving legibility.
- **Monospaced Identifiers**: Standard identifiers and technical payload codes utilize `JetBrains Mono` at `code-snippet` scale for distinct character differentiation.

## Layout & Spacing

Layout operates within a strict 12-column responsive grid adapted for dual-pane workstation utility (form entry on the left, live validation/stepper on the right):

- **Breakpoints**: 
  - Mobile (`<768px`): Fluid single-column stack, collapsible drawer navigation, sticky bottom action bar.
  - Tablet (`768px - 1199px`): 12-column grid with dynamic lateral collapsing for secondary panels.
  - Desktop (`≥1200px`): Dedicated fixed/sticky 3-column wizard stepper (columns 1-3), primary dynamic workspace (columns 4-9), and contextual assistant/summary inspector (columns 10-12) or split 50/50 dual-pane mode for documentation preview.
- **Gutter & Margins**: Grid gutters adhere to standard `1.5rem` (`24px`). Canvas outer margin is `2rem` (`32px`) on desktop viewports and reduces to `1rem` (`16px`) on mobile viewports.
- **Vertical Spacing Cadence**: Component internals use uniform multiples of `0.25rem` (4px). Section dividers within cards maintain a minimum rhythm of `1.5rem` (`space-lg`).

## Elevation & Depth

To preserve an official and audit-ready appearance, the design system avoids heavy shadows, floating blurs, or glow effects:

- **Surface Restraint**: Cards, tables, and stepper panels sit flush on the `#f8fafc` background canvas, segregated using single-pixel borders in Slate 200 (`#e2e8f0`).
- **Resting Depth**: Minimal baseline shadow `0 1px 3px 0 rgba(15, 23, 42, 0.05)` applied to cards to lift actionable panels above static backgrounds.
- **Elevated States**: Dropdowns, context menus, and tooltips receive a controlled shadow `0 4px 6px -1px rgba(15, 23, 42, 0.08), 0 2px 4px -2px rgba(15, 23, 42, 0.04)` combined with an explicit border.
- **Modals & Drawers**: Deep overlay depth `0 20px 25px -5px rgba(15, 23, 42, 0.1), 0 8px 10px -6px rgba(15, 23, 42, 0.06)` with a Slate 900 tint at 40% opacity (`rgba(15, 23, 42, 0.4)`) for the background backdrop.

## Shapes

The geometric framework uses **Soft (`roundedness: 1`)** curves to preserve an authoritative, disciplined document appearance:

- **Standard Elements (`0.25rem` / `4px`)**: Buttons, text inputs, textareas, dynamic list row items, alerts, and tab items.
- **Containers (`0.5rem` / `8px` - `rounded-lg`)**: Primary cards, document preview mockups, modal dialogs, and validation rule containers.
- **Metadata Badges & Pills (`50rem` / Fully rounded)**: Status badges, stage step indicators, and numerical counters use rounded-pill geometry to contrast clearly against rectangular content cards and form boundaries.

## Components

### 1. Buttons
- **Primary**: Background `#0f4c81`, text `#ffffff`, border `#0f4c81`. Hover: `#0b3860`. Focus: ring with `0 0 0 3px rgba(15, 76, 129, 0.25)`.
- **Secondary / Outline**: Background transparent, border `#cbd5e1`, text `#1e293b`. Hover: `#f1f5f9`.
- **Danger**: Border and background `#dc3545`, text `#ffffff`. Hover: `#b02a37`.
- **Size Variants**: `btn-sm` (32px height) for dynamic inline table rows; `btn-md` (40px height) for standard forms; `btn-lg` (48px height) for primary document generation triggers.

### 2. Form Controls & Validation
- **Input Fields & Selects**: Height 40px, background `#ffffff`, border `1px solid #cbd5e1`, border-radius `0.25rem`. Text color `#1e293b`. Focus: border color `#0f4c81`, subtle box-shadow ring.
- **Labels**: Stacked or floating with required markers marked as `<span class="text-danger ms-1">*</span>`. 
- **Validation Messages**: Positioned immediately beneath fields. Incomplete/invalid fields show border `#dc3545`, feedback text `#dc3545` with an SVG error icon.

### 3. Vertical Wizard Stepper
- Sticky navigation rail featuring connected vertical nodes.
- **Completed**: Circular badge (28px) in `#10b981` containing a white checkmark icon; connecting track turns `#10b981`.
- **Active**: Circular badge in `#0f4c81` containing the current step index with white text and a faint outer pulse ring.
- **Pending**: Circular badge in `#f1f5f9` with border `1px solid #cbd5e1` and text `#64748b`.
- **Error / Unresolved**: Circular badge in `#dc3545` containing an exclamation mark.

### 4. Status Badges
- Pill styling (`rounded-pill px-2.5 py-1 text-uppercase`) adhering to `label-micro`:
  - **Borrador**: Background `#f1f5f9`, text `#475569`, border `1px solid #cbd5e1`.
  - **En Revisión**: Background `#fef3c7`, text `#92400e`, border `1px solid #fde68a`.
  - **Validado**: Background `#d1fae5`, text `#065f46`, border `1px solid #a7f3d0`.
  - **Generado**: Background `#e0f2fe`, text `#075985`, border `1px solid #bae6fd`.

### 5. Dynamic List Items (Requirements & Criteria)
- Contained row card with `border: 1px solid #e2e8f0`, background `#ffffff`, and `margin-bottom: 0.5rem`.
- Left-hand drag-and-drop grip handle (`#94a3b8`), followed by an uppercase ID badge (`RF-01`), editable title, priority badge, and right-aligned inline actions (edit icon button, delete button).
- Bottom anchor includes a dashed button (`border: 1px dashed #0f4c81`, background `#f8fafc`) for adding new records.

### 6. AI Assistant Proposal Panel
- Callout card styled with border `1px solid #bae6fd`, top border accent `3px solid #0284c7`, and background `#f0f9ff`.
- Split view comparing original ambiguous requirements against proposed standardized ERS/SRS text (e.g., INCOSE/IEEE compliant).
- Footer contains dual explicit actions: `Aceptar propuesta` (Primary small button) and `Descartar` (Ghost slate button).

### 7. Document Preview (A4 Paginated Card)
- Rendered with an aspect ratio mimicking standard A4 paper (min-height: 842px on standard 595px scale), centered on `#e2e8f0` backdrop with shadow `0 4px 6px -1px rgba(0,0,0,0.1)`.
- Features an institutional header block (logo left, doc ID right, horizontal double rule), formal two-tone table headers (`#f1f5f9` fill with `#1e293b` text), and sign-off signature blocks at the base.