import React from 'react';
import { Menu, Transition } from '@headlessui/react';
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

interface RowActionMenuProps {
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

const RowActionMenu: React.FC<RowActionMenuProps> = ({
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
    <Menu as="div" className="relative inline-block text-left">
      <div>
        <Menu.Button
          disabled={disabled}
          className={classNames(
            'inline-flex w-full justify-center rounded-md bg-white px-3 py-2 text-sm font-medium text-gray-700 shadow-sm ring-1 ring-inset ring-gray-200 hover:bg-gray-50',
            disabled && 'opacity-50 cursor-not-allowed'
          )}
          aria-label="Row actions"
        >
          <EllipsisVerticalIcon className="h-5 w-5" aria-hidden="true" />
        </Menu.Button>
      </div>

      <Transition
        enter="transition ease-out duration-100"
        enterFrom="transform opacity-0 scale-95"
        enterTo="transform opacity-100 scale-100"
        leave="transition ease-in duration-75"
        leaveFrom="transform opacity-100 scale-100"
        leaveTo="transform opacity-0 scale-95"
      >
        <Menu.Items className="absolute right-0 z-10 mt-2 w-56 origin-top-right divide-y divide-gray-100 rounded-md bg-white shadow-lg ring-1 ring-black/5 focus:outline-none">
          <div className="py-1">
            {onToggleExpand && (
              <Menu.Item>
                {({ active }) => (
                  <button
                    onClick={onToggleExpand}
                    className={classNames(
                      active ? 'bg-gray-50 text-gray-900' : 'text-gray-700',
                      'group flex w-full items-center gap-2 px-4 py-2 text-sm'
                    )}
                  >
                    {isExpanded ? (
                      <EyeSlashIcon className="h-5 w-5 text-gray-400 group-hover:text-gray-500" />
                    ) : (
                      <EyeIcon className="h-5 w-5 text-gray-400 group-hover:text-gray-500" />
                    )}
                    {isExpanded ? 'Hide session' : 'Open session'}
                  </button>
                )}
              </Menu.Item>
            )}
            {onUploadPDF && (
              <Menu.Item>
                {({ active }) => (
                  <button
                    onClick={onUploadPDF}
                    className={classNames(
                      active ? 'bg-gray-50 text-gray-900' : 'text-gray-700',
                      'group flex w-full items-center gap-2 px-4 py-2 text-sm'
                    )}
                  >
                    <DocumentArrowUpIcon className="h-5 w-5 text-blue-500" />
                    Upload PDF
                  </button>
                )}
              </Menu.Item>
            )}
            {onManageTools && (
              <Menu.Item>
                {({ active }) => (
                  <button
                    onClick={onManageTools}
                    className={classNames(
                      active ? 'bg-gray-50 text-gray-900' : 'text-gray-700',
                      'group flex w-full items-center gap-2 px-4 py-2 text-sm'
                    )}
                  >
                    <WrenchScrewdriverIcon className="h-5 w-5 text-purple-500" />
                    Manage MCP Tools
                  </button>
                )}
              </Menu.Item>
            )}
          </div>
          <div className="py-1">
            {onToggleSearch && (
              <Menu.Item>
                {({ active }) => (
                  <button
                    onClick={onToggleSearch}
                    className={classNames(
                      active ? 'bg-gray-50 text-gray-900' : 'text-gray-700',
                      'group flex w-full items-center gap-2 px-4 py-2 text-sm'
                    )}
                  >
                    {isSearchEnabled ? (
                      <NoSymbolIcon className="h-5 w-5 text-orange-500" />
                    ) : (
                      <GlobeAltIcon className="h-5 w-5 text-blue-500" />
                    )}
                    {isSearchEnabled ? 'Disable Internet Search' : 'Enable Internet Search'}
                  </button>
                )}
              </Menu.Item>
            )}
            {onToggleActive && (
              <Menu.Item>
                {({ active }) => (
                  <button
                    onClick={onToggleActive}
                    className={classNames(
                      active ? 'bg-gray-50 text-gray-900' : 'text-gray-700',
                      'group flex w-full items-center gap-2 px-4 py-2 text-sm'
                    )}
                  >
                    {isActive ? (
                      <PauseCircleIcon className="h-5 w-5 text-yellow-600" />
                    ) : (
                      <RocketLaunchIcon className="h-5 w-5 text-green-600" />
                    )}
                    {isActive ? 'Disable session' : 'Activate session'}
                  </button>
                )}
              </Menu.Item>
            )}
          </div>
          {onDelete && (
            <div className="py-1">
              <Menu.Item>
                {({ active }) => (
                  <button
                    onClick={onDelete}
                    className={classNames(
                      active ? 'bg-red-50 text-red-700' : 'text-red-600',
                      'group flex w-full items-center gap-2 px-4 py-2 text-sm'
                    )}
                  >
                    <TrashIcon className="h-5 w-5" />
                    Delete session
                  </button>
                )}
              </Menu.Item>
            </div>
          )}
        </Menu.Items>
      </Transition>
    </Menu>
  );
};

export default RowActionMenu;