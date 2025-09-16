import React from 'react';
import { ArrowTrendingUpIcon, UsersIcon, DocumentTextIcon, ChatBubbleBottomCenterTextIcon } from '@heroicons/react/24/outline';

type StatKind = 'users' | 'sessions' | 'documents' | 'messages';

const iconMap: Record<StatKind, React.ReactNode> = {
  users: <UsersIcon className="h-6 w-6 text-purple-600" />,
  sessions: <ArrowTrendingUpIcon className="h-6 w-6 text-blue-600" />,
  documents: <DocumentTextIcon className="h-6 w-6 text-emerald-600" />,
  messages: <ChatBubbleBottomCenterTextIcon className="h-6 w-6 text-orange-600" />,
};

interface StatCardProps {
  label: string;
  value: number | string;
  kind: StatKind;
}

const StatCard: React.FC<StatCardProps> = ({ label, value, kind }) => {
  return (
    <div className="bg-white p-6 rounded-xl shadow-sm ring-1 ring-gray-100">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium text-gray-500">{label}</h3>
        {iconMap[kind]}
      </div>
      <p className="mt-2 text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-gray-900 to-gray-700">
        {value}
      </p>
    </div>
  );
};

export default StatCard;