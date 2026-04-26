# NoteKeeper UI Components

This directory contains reusable UI components following the NoteKeeper Design System.

## Component List

### Buttons
- `Button` - Primary, secondary, ghost, and destructive variants
- `IconButton` - Icon-only buttons with tooltip support
- `ButtonGroup` - Grouped button layouts

### Form Elements
- `Input` - Text input with validation states
- `TextArea` - Multi-line text input for note content
- `Select` - Dropdown select with search
- `TagInput` - Multi-tag input with autocomplete
- `ColorPicker` - Category color selection

### Layout
- `Card` - Note card with hover states
- `Modal` - Dialog overlay with focus trap
- `Drawer` - Slide-out sidebar (mobile navigation)
- `Sidebar` - Main navigation sidebar

### Feedback
- `Toast` - Notification system
- `Skeleton` - Loading placeholders
- `Spinner` - Loading indicators
- `ProgressBar` - Progress indicators

### Data Display
- `Badge` - Category and status badges
- `Tag` - Removable tag pills
- `EmptyState` - Empty list placeholders
- `Avatar` - User avatar with fallback

## Usage Example

```tsx
import { Button, Card, Tag } from '@/components/ui';

function NoteCard({ note }) {
  return (
    <Card className="card-hover">
      <h3>{note.title}</h3>
      <p>{note.preview}</p>
      <div className="flex gap-2">
        {note.tags.map(tag => (
          <Tag key={tag.id}>{tag.name}</Tag>
        ))}
      </div>
      <Button variant="primary">Edit</Button>
    </Card>
  );
}
```

## Styling

All components use CSS custom properties from `styles/tokens.css` for consistent theming.

## Accessibility

- All interactive elements are keyboard accessible
- ARIA attributes for screen readers
- Focus management for modals and dropdowns
- Reduced motion support
