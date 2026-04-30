'use client';

import React, { useState } from 'react';

interface TabItem {
  id: string;
  label: string;
  icon?: React.ReactNode;
  content: React.ReactNode;
}

interface TabsProps {
  items: TabItem[];
  activeTab?: string;
  onChange?: (tabId: string) => void;
  className?: string;
}

function Tabs({
  items,
  activeTab: controlledActive,
  onChange,
  className = '',
}: TabsProps) {
  const [internalActive, setInternalActive] = useState(items[0]?.id);
  const activeTab = controlledActive ?? internalActive;

  const handleChange = (tabId: string) => {
    if (!controlledActive) setInternalActive(tabId);
    onChange?.(tabId);
  };

  const activeItem = items.find((item) => item.id === activeTab);

  return (
    <div className={className}>
      <div className="flex border-b border-border">
        {items.map((item) => (
          <button
            key={item.id}
            onClick={() => handleChange(item.id)}
            className={`
              flex items-center gap-2 px-4 py-2.5 text-sm font-medium
              transition-colors duration-normal focus-ring
              border-b-2 -mb-px
              ${
                activeTab === item.id
                  ? 'text-primary border-primary'
                  : 'text-text-tertiary border-transparent hover:text-text-secondary hover:border-border-hover'
              }
            `}
          >
            {item.icon}
            {item.label}
          </button>
        ))}
      </div>
      <div className="pt-4">{activeItem?.content}</div>
    </div>
  );
}

export { Tabs };
export type { TabsProps, TabItem };
