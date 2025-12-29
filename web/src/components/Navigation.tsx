"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Home,
  MapPin,
  Search,
  Building2,
  BarChart3,
  Bookmark,
  Settings,
  GitBranch,
  DollarSign,
} from "lucide-react";
import { cn } from "@/lib/utils";

const navigation = [
  { name: "Dashboard", href: "/", icon: Home },
  { name: "Markets", href: "/markets", icon: MapPin },
  { name: "Find Deals", href: "/deals", icon: Search },
  { name: "Saved", href: "/saved", icon: Bookmark },
  { name: "Pipeline", href: "/pipeline", icon: GitBranch },
  { name: "Financing", href: "/financing", icon: DollarSign },
  { name: "Analyze", href: "/import", icon: BarChart3 },
];

export function Navigation() {
  const pathname = usePathname();

  return (
    <nav className="bg-white border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex">
            {/* Logo */}
            <Link href="/" className="flex items-center gap-2 px-2">
              <Building2 className="h-8 w-8 text-primary-600" />
              <span className="font-bold text-xl text-gray-900">
                DealFinder
              </span>
            </Link>

            {/* Navigation Links */}
            <div className="hidden sm:ml-8 sm:flex sm:space-x-4">
              {navigation.map((item) => {
                const isActive = pathname === item.href ||
                  (item.href !== "/" && pathname.startsWith(item.href));
                const Icon = item.icon;

                return (
                  <Link
                    key={item.name}
                    href={item.href}
                    className={cn(
                      "inline-flex items-center gap-2 px-3 py-2 text-sm font-medium rounded-md transition-colors",
                      isActive
                        ? "text-primary-600 bg-primary-50"
                        : "text-gray-600 hover:text-gray-900 hover:bg-gray-50"
                    )}
                  >
                    <Icon className="h-4 w-4" />
                    {item.name}
                  </Link>
                );
              })}
            </div>
          </div>

          {/* Right side - Admin */}
          <div className="hidden sm:flex items-center">
            <Link
              href="/admin/jobs"
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-md transition-colors"
            >
              <Settings className="h-4 w-4" />
              Admin
            </Link>
          </div>
        </div>
      </div>

      {/* Mobile navigation */}
      <div className="sm:hidden border-t border-gray-200">
        <div className="flex justify-around py-2">
          {navigation.map((item) => {
            const isActive = pathname === item.href;
            const Icon = item.icon;

            return (
              <Link
                key={item.name}
                href={item.href}
                className={cn(
                  "flex flex-col items-center gap-1 px-3 py-2 text-xs font-medium",
                  isActive
                    ? "text-primary-600"
                    : "text-gray-600"
                )}
              >
                <Icon className="h-5 w-5" />
                {item.name}
              </Link>
            );
          })}
        </div>
      </div>
    </nav>
  );
}
