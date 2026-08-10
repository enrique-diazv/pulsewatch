import { useEffect, useRef } from 'react'

interface ConfirmDialogProps {
  open: boolean
  title: string
  description: string
  confirmLabel: string
  pending?: boolean
  onCancel: () => void
  onConfirm: () => void
}

export function ConfirmDialog({
  open,
  title,
  description,
  confirmLabel,
  pending = false,
  onCancel,
  onConfirm,
}: ConfirmDialogProps) {
  const dialogRef = useRef<HTMLDialogElement>(null)

  useEffect(() => {
    const dialog = dialogRef.current

    if (!dialog) {
      return
    }

    if (open && !dialog.open) {
      dialog.showModal()
    }

    if (!open && dialog.open) {
      dialog.close()
    }
  }, [open])

  return (
    <dialog
      aria-describedby="confirm-dialog-description"
      aria-labelledby="confirm-dialog-title"
      className="confirm-dialog"
      onCancel={(event) => {
        event.preventDefault()

        if (!pending) {
          onCancel()
        }
      }}
      ref={dialogRef}
    >
      <div className="confirm-dialog__content">
        <p className="page-eyebrow">Confirmation required</p>
        <h2 id="confirm-dialog-title">{title}</h2>
        <p id="confirm-dialog-description">
          {description}
        </p>

        <div className="confirm-dialog__actions">
          <button
            autoFocus
            className="button button--secondary"
            disabled={pending}
            onClick={onCancel}
            type="button"
          >
            Cancel
          </button>
          <button
            className="button button--danger"
            disabled={pending}
            onClick={onConfirm}
            type="button"
          >
            {pending ? 'Deleting...' : confirmLabel}
          </button>
        </div>
      </div>
    </dialog>
  )
}