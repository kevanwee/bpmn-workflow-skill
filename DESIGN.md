---
name: BPMN Workflow
description: A quiet working surface for inspecting and editing BPMN diagrams.
colors:
  green: "#205644"
  green-hover: "#133f30"
  ink: "#19352d"
  muted-ink: "#405c50"
  page: "#f5f8f5"
  header: "#edf4ee"
  canvas: "white"
  line: "#d6e1d9"
  control-border: "#acbfb1"
  control-hover: "#e3eee6"
  focus: "#347950"
  selection: "#bed9c8"
  selection-ink: "#112d23"
  error: "#9c2530"
  error-surface: "#fff2f1"
  scrollbar: "#9cb5a5"
typography:
  headline:
    fontFamily: "ui-sans-serif, system-ui, sans-serif"
    fontSize: "26px"
    fontWeight: 700
    lineHeight: 1.2
    letterSpacing: "-.025em"
  title:
    fontFamily: "ui-sans-serif, system-ui, sans-serif"
    fontSize: "16px"
    fontWeight: 700
  body:
    fontFamily: "ui-sans-serif, system-ui, sans-serif"
    fontSize: "14px"
    lineHeight: 1.6
  label:
    fontFamily: "ui-sans-serif, system-ui, sans-serif"
    fontSize: "14px"
  status:
    fontFamily: "ui-sans-serif, system-ui, sans-serif"
    fontSize: "13px"
rounded:
  button: "6px"
  field: "5px"
spacing:
  toolbar-gap: "8px"
  header-gap: "24px"
  inspector: "24px"
  field: "10px"
components:
  button-primary:
    backgroundColor: "{colors.green}"
    textColor: "{colors.canvas}"
    rounded: "{rounded.button}"
    padding: ".65rem .9rem"
  button-primary-hover:
    backgroundColor: "{colors.green-hover}"
  button-secondary:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.ink}"
    rounded: "{rounded.button}"
    padding: ".65rem .9rem"
  button-secondary-hover:
    backgroundColor: "{colors.control-hover}"
  field:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.ink}"
    rounded: "{rounded.field}"
    padding: "{spacing.field}"
    width: "100%"
  status:
    textColor: "{colors.muted-ink}"
    typography: "{typography.status}"
    padding: "12px 24px"
---

# Design System: BPMN Workflow

## Overview

**Creative North Star: "The quiet working surface"**

This phrase describes the inherited direction recorded in PRODUCT.md, rather than a new identity. Near-white surfaces, dark green ink and restrained green actions frame an immediately available diagram. The canvas is the main working area; the shell supplies compact controls and readable context.

This document records the shipped editor in `skills/bpmn-workflow/editor`, checked against the desktop and mobile review captures listed in `docs/screenshots.json`. The bpmn.io canvas, palette, symbols and attribution remain the upstream visual system; the shell does not redefine BPMN notation.

**Key Characteristics:**
- A large white diagram canvas with a narrow contextual inspector.
- A compact, wrapping toolbar with restrained green primary actions.
- System typography, thin borders and flat surfaces.
- A visible editing boundary and persistent status feedback.

## Colors

The palette is a subdued green accent with green-tinted neutrals. The frontmatter records the exact shipped values.

### Primary

- **Working green** (`green`): Download BPMN and Apply to element actions; also the text-input caret through the CSS custom property.
- **Deep working green** (`green-hover`): Primary-action hover state.
- **Focus green** (`focus`): Visible keyboard outline for controls and the file-open label.

### Neutral

- **Dark green ink** (`ink`) and **muted green ink** (`muted-ink`): Main labels and secondary explanatory/status text.
- **Near-white page** (`page`), **pale green header** (`header`) and **white canvas** (`canvas`): Separate working regions without depth effects.
- **Quiet divider** (`line`) and **control border** (`control-border`): Regional separation and control edges; the palette border also uses the control-border value.
- **Soft hover** (`control-hover`): Secondary-action hover feedback.
- **Selection wash** (`selection`) and **selection ink** (`selection-ink`): Browser text selection.
- **Scrollbar green** (`scrollbar`): Thin scrollbar thumb over the header-colored track.

The error pair (`error`, `error-surface`) is semantic feedback in the status strip, not an additional brand accent.

**The Canvas Rule.** Keep shell colors separate from the upstream diagram notation; preserve bpmn.io's familiar symbols and attribution.

## Typography

The shell uses the system sans-serif stack throughout, including inherited button and form-control text. There is no display face, custom webfont or monospace role.

- **Headline:** The page title uses the frontmatter headline role.
- **Title:** Inspector and editing-boundary headings use the title role.
- **Body:** Inspector paragraphs use the body role. Header supporting text also uses the label size, with normal browser line height.
- **Label:** Form labels use the label role; desktop controls inherit the root browser size, while mobile toolbar controls explicitly use the label size.
- **Status:** Persistent feedback uses the status role.

Diagram text is rendered by bpmn.io and is outside the shell's typography scale. Fit-to-viewport can make a large process's labels very small; users can zoom for detail.

## Layout

The desktop header is a horizontal flex layout with title and supporting line on the left and wrapping actions on the right. It uses (20px 28px) padding and the header-gap token. The main layout has a flexible canvas column and a fixed (300px) inspector. The inspector uses its spacing token and a left divider.

The desktop canvas height is `calc(100vh - 154px)` with a (440px) minimum. The main region has `min-height: calc(100vh - 110px)`. A status strip sits below the canvas. These are current implementation formulas, not guarantees that content always fits the viewport.

At (800px) and below, the header stacks with (18px) padding and a (16px) gap; toolbar controls wrap naturally. The main grid becomes one column, with the inspector below the canvas, a top divider and (20px) padding. The canvas uses (60vh) height with a (380px) minimum. Toolbar buttons use (.6rem .7rem) padding and the label type size. The mobile page scrolls vertically to reach the inspector and boundary copy.

## Elevation & Depth

The custom shell is flat and defines no shadows. Pale surfaces, thin borders and whitespace distinguish regions. Upstream bpmn.io owns its palette, context actions and diagram interaction treatments.

## Shapes

Buttons have gently rounded corners using the button radius; editable text fields use the field radius. Controls have a single-pixel border. Regional containers are rectangular with divider lines rather than floating cards. BPMN event circles, gateway diamonds, activities and connectors retain upstream notation.

## Components

### Buttons and toolbar

Secondary controls are white with ink text and a control border; Download BPMN and the inspector submit button use working green with white text. Hover fills follow the frontmatter variants. Focus uses a (3px) outline with a (3px) offset. Disabled buttons use half opacity and a wait cursor. Background-color transitions last (.16s), ease out, and apply only when reduced motion is not requested. No custom active-state styling is defined.

The toolbar is action navigation, with an (8px) gap and wrapping. Open BPMN is a styled label bound to a visually hidden file input; focus on the file input outlines the label. There are no navigation tabs, chips or card components.

### Inspector fields

Name and Instructions and context are full-width white fields with the field radius and padding, a control border and ink text. Labels sit (18px) above and (7px) below their preceding boundary. The textarea has seven rows and resizes vertically. The Apply to element button has a (12px) top margin.

The form appears for an editable selection. Multiple imported documentation entries reveal a native browser select, which intentionally has no custom field styling in this extraction. Changing its entry changes the text shown; applying an edit preserves the other entries. Do not imply custom styling or a custom select interaction exists.

### Status and editing boundary

The status strip has a top divider and the frontmatter status padding. It announces import, edit and export state through a polite live region; errors use the semantic error pair. The boundary is separated by a top divider, (24px) top padding and (36px) top margin, reduced to (24px) margin on mobile. Keep its browser-storage and non-execution explanation readable and visible in the document flow.

## Do's and Don'ts

### Do:
- **Do** preserve the inherited white/green shell and original bpmn.io notation.
- **Do** keep the canvas dominant and allow toolbar controls to wrap on narrow screens.
- **Do** preserve visible keyboard focus, reduced-motion handling and persistent status feedback.
- **Do** keep editing limits and the illustrative nature of the example visible.

### Don't:
- **Don't** add decorative shadows, cards or display fonts to this scoped extraction.
- **Don't** recolor BPMN notation to match the shell accent or remove upstream attribution.
- **Don't** present diagram validation or editing as task execution or proof of business outcomes.
- **Don't** describe the native documentation-entry select as a custom styled field.
