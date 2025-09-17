import React from 'react';
import {
  EllipsisVerticalIcon,
  EyeIcon,
  EyeSlashIcon,
  DocumentArrowUpIcon,
  WrenchScrewdriverIcon,
  TrashIcon,
  RocketLaunchIcon,
  PauseCircleIcon,
  GlobeAltIcon,
  NoSymbolIcon,
} from '@heroicons/react/24/outline';

interface RowActionBarProps {
  isExpanded?: boolean;
  onToggleExpand?: () => void;

  isActive?: boolean;
  onToggleActive?: () => void;

  isSearchEnabled?: boolean;
  onToggleSearch?: () => void;

  onUploadPDF?: () => void;
  onManageTools?: () => void;
  onDelete?: () => void;
  disabled?: boolean;
}

function classNames(...classes: (string | false | null | undefined)[]) {
  return classes.filter(Boolean).join(' ');
}

// Inline action bar to replace dropdown menu for better visibility
const RowActionBar: React.FC<RowActionBarProps> = ({
  isExpanded,
  onToggleExpand,
  isActive,
  onToggleActive,
  isSearchEnabled,
  onToggleSearch,
  onUploadPDF,
  onManageTools,
  onDelete,
  disabled,
}) => {
  return (
    <div className="flex flex-wrap gap-2 items-center">
      {onToggleExpand && (
        <button
          type="button"
          disabled={disabled}
          onClick={onToggleExpand}
          className={classNames(
            'inline-flex items-center gap-1 rounded-md border border-gray-300 bg-white px-3 py-1.5 text-xs font-medium text-gray-700 shadow-sm hover:bg-gray-50',
            disabled && 'opacity-50 cursor-not-allowed'
          )}
          aria-label={isExpanded ? 'Hide session' : 'Open session'}
          title={isExpanded ? 'Hide session' : 'Open session'}
        >
          {isExpanded ? (
            <EyeSlashIcon className="h-4 w-4" />
          ) : (
            <EyeIcon className="h-4 w-4" />
          )}
          <span>{isExpanded ? 'Hide' : 'Open'}</span>
        </button>
      )}

      {onToggleSearch && (
        <button
          type="button"
          disabled={disabled}
          onClick={onToggleSearch}
          className={classNames(
            'inline-flex items-center gap-1 rounded-md border border-gray-300 bg-white px-3 py-1.5 text-xs font-medium text-gray-700 shadow-sm hover:bg-gray-50',
            disabled && 'opacity-50 cursor-not-allowed'
          )}
          aria-label={isSearchEnabled ? 'Disable Internet Search' : 'Enable Internet Search'}
          title={isSearchEnabled ? 'Disable Internet Search' : 'Enable Internet Search'}
        >
          {isSearchEnabled ? (
            <NoSymbolIcon className="h-4 w-4 text-orange-600" />
          ) : (
            <GlobeAltIcon className="h-4 w-4 text-blue-600" />
          )}
          <span>{isSearchEnabled ? 'Search Off' : 'Search On'}</span>
        </button>
      )}

      {onToggleActive && (
        <button
          type="button"
          disabled={disabled}
          onClick={onToggleActive}
          className={classNames(
            'inline-flex items-center gap-1 rounded-md border border-gray-300 bg-white px-3 py-1.5 text-xs font-medium text-gray-700 shadow-sm hover:bg-gray-50',
            disabled && 'opacity-50 cursor-not-allowed'
          )}
          aria-label={isActive ? 'Disable session' : 'Activate session'}
          title={isActive ? 'Disable session' : 'Activate session'}
        >
          {isActive ? (
            <PauseCircleIcon className="h-4 w-4 text-yellow-600" />
          ) : (
            <RocketLaunchIcon className="h-4 w-4 text-green-600" />
          )}
          <span>{isActive ? 'Disable' : 'Activate'}</span>
        </button>
      )}

      {onUploadPDF && (
        <button
          type="button"
          disabled={disabled}
          onClick={onUploadPDF}
          className={classNames(
            'inline-flex items-center gap-1 rounded-md border border-gray-300 bg-white px-3 py-1.5 text-xs font-medium text-gray-700 shadow-sm hover:bg-gray-50',
            disabled && 'opacity-50 cursor-not-allowed'
          )}
          aria-label="Upload PDF"
          title="Upload PDF"
        >
          <DocumentArrowUpIcon className="h-4 w-4 text-blue-600" />
          <span>Upload</span>
        </button>
      )}

      {onManageTools && (
        <button
          type="button"
          disabled={disabled}
          onClick={onManageTools}
          className={classNames(
            'inline-flex items-center gap-1 rounded-md border border-gray-300 bg-white px-3 py-1.5 text-xs font-medium text-gray-700 shadow-sm hover:bg-gray-50',
            disabled && 'opacity-50 cursor-not-allowed'
          )}
          aria-label="Manage MCP Tools"
          title="Manage MCP Tools"
        >
          <WrenchScrewdriverIcon className="h-4 w-4 text-purple-600" />
          <span>Tools</span>
        </button>
      )}

      {onDelete && (
        <button
          type="button"
          disabled={disabled}
          onClick={onDelete}
          className={classNames(
            'inline-flex items-center gap-1 rounded-md border border-red-300 bg-white px-3 py-1.5 text-xs font-medium text-red-700 shadow-sm hover:bg-red-50',
            disabled && 'opacity-50 cursor-not-allowed'
          )}
          aria-label="Delete session"
          title="Delete session"
        >
          <TrashIcon className="h-4 w-4" />
          <span>Delete</span>
        </button>
      )}
    </div>
  );
};

export default RowActionBar;