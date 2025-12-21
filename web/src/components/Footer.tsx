import { Building2, Github, ExternalLink } from "lucide-react";

export function Footer() {
  return (
    <footer className="bg-white border-t border-gray-200 mt-auto">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="flex flex-col sm:flex-row justify-between items-center gap-4">
          {/* Branding */}
          <div className="flex items-center gap-2 text-gray-600">
            <Building2 className="h-5 w-5 text-primary-600" />
            <span className="font-semibold">DealFinder</span>
            <span className="text-gray-400">|</span>
            <span className="text-sm">Real Estate Investment Analysis</span>
          </div>

          {/* Data Sources */}
          <div className="flex items-center gap-4 text-xs text-gray-500">
            <span className="flex items-center gap-1">
              Data from:
            </span>
            <a
              href="https://fred.stlouisfed.org"
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-primary-600 flex items-center gap-1"
            >
              FRED
              <ExternalLink className="h-3 w-3" />
            </a>
            <span className="text-gray-300">|</span>
            <a
              href="https://www.redfin.com/news/data-center/"
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-primary-600 flex items-center gap-1"
            >
              Redfin
              <ExternalLink className="h-3 w-3" />
            </a>
            <span className="text-gray-300">|</span>
            <a
              href="https://www.hud.gov/program_offices/public_indian_housing/programs/hcv/landlord/fmr"
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-primary-600 flex items-center gap-1"
            >
              HUD FMR
              <ExternalLink className="h-3 w-3" />
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
}
