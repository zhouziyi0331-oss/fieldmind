import { useState, useCallback } from 'react';

export interface ConfirmDialogOptions {
  title: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  type?: 'warning' | 'danger' | 'info';
}

export interface ConfirmDialogState extends ConfirmDialogOptions {
  isOpen: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}

export const useConfirmDialog = () => {
  const [dialogState, setDialogState] = useState<ConfirmDialogState | null>(null);

  const showConfirmDialog = useCallback((options: ConfirmDialogOptions): Promise<boolean> => {
    return new Promise((resolve) => {
      const handleConfirm = () => {
        setDialogState(null);
        resolve(true);
      };

      const handleCancel = () => {
        setDialogState(null);
        resolve(false);
      };

      setDialogState({
        ...options,
        isOpen: true,
        onConfirm: handleConfirm,
        onCancel: handleCancel,
      });
    });
  }, []);

  const closeDialog = useCallback(() => {
    if (dialogState) {
      dialogState.onCancel();
    }
  }, [dialogState]);

  return {
    dialogState,
    showConfirmDialog,
    closeDialog,
  };
};
