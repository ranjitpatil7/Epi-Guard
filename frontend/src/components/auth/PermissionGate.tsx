import React from 'react';
import { useAuth } from '../../lib/auth/AuthContext';
import { Permission } from '../../lib/auth/permissions';

interface PermissionGateProps {
  permission: Permission | Permission[];
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

export const PermissionGate: React.FC<PermissionGateProps> = ({ 
  permission, 
  children, 
  fallback = null 
}) => {
  const { hasPermission, isLoading } = useAuth();

  if (isLoading) return null;

  const permissionsToCheck = Array.isArray(permission) ? permission : [permission];
  const hasAccess = permissionsToCheck.every(p => hasPermission(p));

  if (!hasAccess) {
    return <>{fallback}</>;
  }

  return <>{children}</>;
};
