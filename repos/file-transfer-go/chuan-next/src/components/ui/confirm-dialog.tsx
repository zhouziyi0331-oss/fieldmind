"use client";

import React from 'react';
import { Button } from '@/components/ui/button';
import { AlertTriangle, Wifi, WifiOff } from 'lucide-react';

interface ConfirmDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  type?: 'warning' | 'danger' | 'info';
}

export function ConfirmDialog({
  isOpen,
  onClose,
  onConfirm,
  title,
  message,
  confirmText = '确认',
  cancelText = '取消',
  type = 'warning'
}: ConfirmDialogProps) {
  const handleConfirm = () => {
    onConfirm();
    onClose();
  };

  const handleCancel = () => {
    onClose();
  };

  const getIcon = () => {
    switch (type) {
      case 'danger':
        return <WifiOff className="w-6 h-6 text-red-500" />;
      case 'warning':
        return <AlertTriangle className="w-6 h-6 text-yellow-500" />;
      case 'info':
        return <Wifi className="w-6 h-6 text-blue-500" />;
      default:
        return <AlertTriangle className="w-6 h-6 text-yellow-500" />;
    }
  };

  const getButtonStyles = () => {
    switch (type) {
      case 'danger':
        return 'bg-gradient-to-r from-red-500 to-red-600 hover:from-red-600 hover:to-red-700';
      case 'warning':
        return 'bg-gradient-to-r from-yellow-500 to-orange-500 hover:from-yellow-600 hover:to-orange-600';
      case 'info':
        return 'bg-gradient-to-r from-blue-500 to-indigo-500 hover:from-blue-600 hover:to-indigo-600';
      default:
        return 'bg-gradient-to-r from-yellow-500 to-orange-500 hover:from-yellow-600 hover:to-orange-600';
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-white/95 backdrop-blur-md rounded-2xl shadow-2xl border border-white/20 max-w-md w-full mx-4 animate-in zoom-in-95 duration-200">
        {/* Header */}
        <div className="flex items-center space-x-4 p-6 pb-4">
          <div className="flex-shrink-0">
            {getIcon()}
          </div>
          <div>
            <h3 className="text-lg font-semibold text-slate-800">
              {title}
            </h3>
          </div>
        </div>

        {/* Content */}
        <div className="px-6 pb-6">
          <p className="text-slate-600 leading-relaxed">
            {message}
          </p>
        </div>

        {/* Actions */}
        <div className="flex items-center justify-end space-x-3 px-6 pb-6">
          <Button
            variant="outline"
            onClick={handleCancel}
            className="px-6 py-2 border-slate-200 text-slate-600 hover:text-slate-800 hover:border-slate-300 rounded-lg"
          >
            {cancelText}
          </Button>
          <Button
            onClick={handleConfirm}
            className={`px-6 py-2 text-white font-medium rounded-lg shadow-lg transition-all duration-200 hover:shadow-xl ${getButtonStyles()}`}
          >
            {confirmText}
          </Button>
        </div>
      </div>
    </div>
  );
}
