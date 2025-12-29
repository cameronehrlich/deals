"use client";

import { useEffect, useState, useCallback } from "react";
import {
  DollarSign,
  Building2,
  Users,
  Plus,
  Edit3,
  Trash2,
  Phone,
  Mail,
  Globe,
  Star,
  ChevronDown,
  ChevronUp,
  Loader2,
  CheckCircle,
  AlertTriangle,
  Calculator,
  FileText,
  RefreshCw,
} from "lucide-react";
import { api } from "@/lib/api";
import { LoadingPage } from "@/components/LoadingSpinner";
import { cn, formatCurrency, formatPercent } from "@/lib/utils";

// Types for financing desk
interface BorrowerProfile {
  id: string;
  full_name?: string;
  email?: string;
  phone?: string;
  credit_score?: number;
  annual_income?: number;
  total_assets?: number;
  properties_owned?: number;
  investment_experience?: string;
  preferred_loan_types?: string[];
  notes?: string;
}

interface Lender {
  id: string;
  name: string;
  lender_type: string;
  contact_name?: string;
  contact_email?: string;
  contact_phone?: string;
  website?: string;
  loan_types?: string[];
  min_credit_score?: number;
  min_down_payment?: number;
  max_ltv?: number;
  rate_range_low?: number;
  rate_range_high?: number;
  notes?: string;
  is_active: boolean;
}

interface LenderQuote {
  id: string;
  lender_id: string;
  property_id?: string;
  loan_amount: number;
  interest_rate: number;
  loan_term_years: number;
  points?: number;
  origination_fee?: number;
  closing_costs?: number;
  monthly_payment?: number;
  apr?: number;
  rate_lock_days?: number;
  status: string;
  notes?: string;
  quoted_at: string;
}

// Borrower Profile Card
function BorrowerProfileCard({
  profile,
  onEdit,
  loading,
}: {
  profile: BorrowerProfile | null;
  onEdit: () => void;
  loading: boolean;
}) {
  if (loading) {
    return (
      <div className="card">
        <div className="flex items-center justify-center py-8">
          <Loader2 className="h-6 w-6 animate-spin text-primary-500" />
        </div>
      </div>
    );
  }

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
          <Users className="h-5 w-5 text-primary-600" />
          Borrower Profile
        </h3>
        <button onClick={onEdit} className="btn-secondary text-sm">
          <Edit3 className="h-4 w-4 mr-1" />
          Edit
        </button>
      </div>

      {!profile?.full_name ? (
        <div className="text-center py-6 text-gray-500">
          <Users className="h-8 w-8 mx-auto mb-2 opacity-50" />
          <p>No profile set up yet</p>
          <button onClick={onEdit} className="mt-2 text-primary-600 hover:text-primary-700 text-sm">
            Create your borrower profile
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-gray-500">Name</p>
              <p className="font-medium">{profile.full_name}</p>
            </div>
            {profile.credit_score && (
              <div>
                <p className="text-sm text-gray-500">Credit Score</p>
                <p
                  className={cn(
                    "font-medium",
                    profile.credit_score >= 740
                      ? "text-green-600"
                      : profile.credit_score >= 680
                      ? "text-amber-600"
                      : "text-red-600"
                  )}
                >
                  {profile.credit_score}
                </p>
              </div>
            )}
            {profile.annual_income && (
              <div>
                <p className="text-sm text-gray-500">Annual Income</p>
                <p className="font-medium">{formatCurrency(profile.annual_income)}</p>
              </div>
            )}
            {profile.total_assets && (
              <div>
                <p className="text-sm text-gray-500">Total Assets</p>
                <p className="font-medium">{formatCurrency(profile.total_assets)}</p>
              </div>
            )}
            {profile.properties_owned !== undefined && (
              <div>
                <p className="text-sm text-gray-500">Properties Owned</p>
                <p className="font-medium">{profile.properties_owned}</p>
              </div>
            )}
            {profile.investment_experience && (
              <div>
                <p className="text-sm text-gray-500">Experience</p>
                <p className="font-medium capitalize">{profile.investment_experience}</p>
              </div>
            )}
          </div>

          {profile.preferred_loan_types && profile.preferred_loan_types.length > 0 && (
            <div>
              <p className="text-sm text-gray-500 mb-1">Preferred Loan Types</p>
              <div className="flex flex-wrap gap-1">
                {profile.preferred_loan_types.map((type) => (
                  <span key={type} className="px-2 py-0.5 bg-primary-100 text-primary-700 rounded-full text-xs">
                    {type}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// Lender Card
function LenderCard({
  lender,
  onEdit,
  onDelete,
}: {
  lender: Lender;
  onEdit: () => void;
  onDelete: () => void;
}) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className={cn("border rounded-lg p-4", !lender.is_active && "opacity-60")}>
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-full bg-primary-100 flex items-center justify-center">
            <Building2 className="h-5 w-5 text-primary-600" />
          </div>
          <div>
            <h4 className="font-medium text-gray-900">{lender.name}</h4>
            <p className="text-sm text-gray-500 capitalize">{lender.lender_type.replace("_", " ")}</p>
          </div>
        </div>
        <div className="flex items-center gap-1">
          <button onClick={onEdit} className="p-1 text-gray-400 hover:text-primary-600">
            <Edit3 className="h-4 w-4" />
          </button>
          <button onClick={onDelete} className="p-1 text-gray-400 hover:text-red-600">
            <Trash2 className="h-4 w-4" />
          </button>
          <button onClick={() => setExpanded(!expanded)} className="p-1 text-gray-400">
            {expanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
          </button>
        </div>
      </div>

      {/* Rate Range */}
      {(lender.rate_range_low || lender.rate_range_high) && (
        <div className="mt-3 flex items-center gap-4 text-sm">
          <span className="text-gray-500">Rates:</span>
          <span className="font-medium">
            {lender.rate_range_low ? formatPercent(lender.rate_range_low / 100) : "?"}
            {" - "}
            {lender.rate_range_high ? formatPercent(lender.rate_range_high / 100) : "?"}
          </span>
          {lender.min_credit_score && (
            <>
              <span className="text-gray-300">|</span>
              <span className="text-gray-500">Min Credit:</span>
              <span className="font-medium">{lender.min_credit_score}</span>
            </>
          )}
        </div>
      )}

      {expanded && (
        <div className="mt-4 pt-4 border-t space-y-3">
          {lender.contact_name && (
            <div className="text-sm">
              <span className="text-gray-500">Contact:</span>{" "}
              <span className="font-medium">{lender.contact_name}</span>
            </div>
          )}
          <div className="flex flex-wrap gap-3 text-sm">
            {lender.contact_email && (
              <a href={`mailto:${lender.contact_email}`} className="flex items-center gap-1 text-gray-600 hover:text-primary-600">
                <Mail className="h-3 w-3" />
                {lender.contact_email}
              </a>
            )}
            {lender.contact_phone && (
              <a href={`tel:${lender.contact_phone}`} className="flex items-center gap-1 text-gray-600 hover:text-primary-600">
                <Phone className="h-3 w-3" />
                {lender.contact_phone}
              </a>
            )}
            {lender.website && (
              <a href={lender.website} target="_blank" rel="noopener noreferrer" className="flex items-center gap-1 text-gray-600 hover:text-primary-600">
                <Globe className="h-3 w-3" />
                Website
              </a>
            )}
          </div>
          {lender.loan_types && lender.loan_types.length > 0 && (
            <div>
              <p className="text-sm text-gray-500 mb-1">Loan Types</p>
              <div className="flex flex-wrap gap-1">
                {lender.loan_types.map((type) => (
                  <span key={type} className="px-2 py-0.5 bg-gray-100 text-gray-600 rounded-full text-xs">
                    {type}
                  </span>
                ))}
              </div>
            </div>
          )}
          {lender.notes && <p className="text-sm text-gray-600">{lender.notes}</p>}
        </div>
      )}
    </div>
  );
}

// Quote Card
function QuoteCard({
  quote,
  lender,
}: {
  quote: LenderQuote;
  lender?: Lender;
}) {
  const statusColors: Record<string, string> = {
    pending: "bg-yellow-100 text-yellow-700",
    approved: "bg-green-100 text-green-700",
    declined: "bg-red-100 text-red-700",
    expired: "bg-gray-100 text-gray-700",
  };

  return (
    <div className="border rounded-lg p-4">
      <div className="flex items-start justify-between">
        <div>
          <h4 className="font-medium text-gray-900">{lender?.name || "Unknown Lender"}</h4>
          <p className="text-sm text-gray-500">
            {formatCurrency(quote.loan_amount)} @ {formatPercent(quote.interest_rate / 100)} for {quote.loan_term_years} years
          </p>
        </div>
        <span className={cn("px-2 py-0.5 rounded-full text-xs font-medium", statusColors[quote.status] || statusColors.pending)}>
          {quote.status}
        </span>
      </div>

      <div className="mt-3 grid grid-cols-3 gap-4 text-sm">
        {quote.monthly_payment && (
          <div>
            <p className="text-gray-500">Monthly</p>
            <p className="font-semibold">{formatCurrency(quote.monthly_payment)}</p>
          </div>
        )}
        {quote.apr && (
          <div>
            <p className="text-gray-500">APR</p>
            <p className="font-semibold">{formatPercent(quote.apr / 100)}</p>
          </div>
        )}
        {quote.points !== undefined && (
          <div>
            <p className="text-gray-500">Points</p>
            <p className="font-semibold">{quote.points}</p>
          </div>
        )}
      </div>

      <p className="mt-2 text-xs text-gray-400">
        Quoted {new Date(quote.quoted_at).toLocaleDateString()}
        {quote.rate_lock_days && ` - ${quote.rate_lock_days} day lock`}
      </p>
    </div>
  );
}

// Modal Component
function Modal({
  title,
  children,
  onClose,
}: {
  title: string;
  children: React.ReactNode;
  onClose: () => void;
}) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
      <div className="bg-white rounded-lg shadow-xl max-w-lg w-full max-h-[90vh] overflow-auto">
        <div className="flex items-center justify-between p-4 border-b">
          <h3 className="text-lg font-semibold">{title}</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <span className="sr-only">Close</span>
            &times;
          </button>
        </div>
        <div className="p-4">{children}</div>
      </div>
    </div>
  );
}

export default function FinancingDeskPage() {
  const [loading, setLoading] = useState(true);
  const [borrowerProfile, setBorrowerProfile] = useState<BorrowerProfile | null>(null);
  const [lenders, setLenders] = useState<Lender[]>([]);
  const [quotes, setQuotes] = useState<LenderQuote[]>([]);

  // Modal states
  const [showProfileModal, setShowProfileModal] = useState(false);
  const [showLenderModal, setShowLenderModal] = useState(false);
  const [editingLender, setEditingLender] = useState<Lender | null>(null);

  // Form states
  const [profileForm, setProfileForm] = useState<Partial<BorrowerProfile>>({});
  const [lenderForm, setLenderForm] = useState<Partial<Lender>>({
    lender_type: "bank",
    is_active: true,
  });

  // Fetch data
  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      const [profileData, lendersData, quotesData] = await Promise.all([
        api.getBorrowerProfile().catch(() => null),
        api.getLenders().catch(() => []),
        api.getLenderQuotes().catch(() => []),
      ]);
      setBorrowerProfile(profileData);
      setLenders(lendersData);
      setQuotes(quotesData);
    } catch (err) {
      console.error("Failed to fetch financing data:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Save borrower profile
  const handleSaveProfile = async () => {
    try {
      const saved = await api.saveBorrowerProfile(profileForm);
      setBorrowerProfile(saved);
      setShowProfileModal(false);
    } catch (err) {
      console.error("Failed to save profile:", err);
    }
  };

  // Save lender
  const handleSaveLender = async () => {
    try {
      if (editingLender) {
        const updated = await api.updateLender(editingLender.id, lenderForm);
        setLenders(lenders.map((l) => (l.id === updated.id ? updated : l)));
      } else {
        const created = await api.createLender(lenderForm as any);
        setLenders([created, ...lenders]);
      }
      setShowLenderModal(false);
      setEditingLender(null);
      setLenderForm({ lender_type: "bank", is_active: true });
    } catch (err) {
      console.error("Failed to save lender:", err);
    }
  };

  // Delete lender
  const handleDeleteLender = async (lender: Lender) => {
    if (!confirm(`Delete ${lender.name}?`)) return;
    try {
      await api.deleteLender(lender.id);
      setLenders(lenders.filter((l) => l.id !== lender.id));
    } catch (err) {
      console.error("Failed to delete lender:", err);
    }
  };

  // Open edit lender modal
  const openEditLender = (lender: Lender) => {
    setEditingLender(lender);
    setLenderForm(lender);
    setShowLenderModal(true);
  };

  // Open edit profile modal
  const openEditProfile = () => {
    setProfileForm(borrowerProfile || {});
    setShowProfileModal(true);
  };

  if (loading) {
    return <LoadingPage />;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Financing Desk</h1>
        <p className="text-gray-500 mt-1">Manage your borrower profile, lenders, and loan quotes</p>
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        {/* Borrower Profile */}
        <div className="lg:col-span-1">
          <BorrowerProfileCard profile={borrowerProfile} onEdit={openEditProfile} loading={false} />
        </div>

        {/* Lender Directory */}
        <div className="lg:col-span-2">
          <div className="card">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                <Building2 className="h-5 w-5 text-primary-600" />
                Lender Directory
                <span className="ml-2 px-2 py-0.5 bg-primary-100 text-primary-700 rounded-full text-sm">
                  {lenders.length}
                </span>
              </h3>
              <button
                onClick={() => {
                  setEditingLender(null);
                  setLenderForm({ lender_type: "bank", is_active: true });
                  setShowLenderModal(true);
                }}
                className="btn-primary text-sm"
              >
                <Plus className="h-4 w-4 mr-1" />
                Add Lender
              </button>
            </div>

            {lenders.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <Building2 className="h-8 w-8 mx-auto mb-2 opacity-50" />
                <p>No lenders yet</p>
                <button
                  onClick={() => setShowLenderModal(true)}
                  className="mt-2 text-primary-600 hover:text-primary-700 text-sm"
                >
                  Add your first lender
                </button>
              </div>
            ) : (
              <div className="space-y-3">
                {lenders.map((lender) => (
                  <LenderCard
                    key={lender.id}
                    lender={lender}
                    onEdit={() => openEditLender(lender)}
                    onDelete={() => handleDeleteLender(lender)}
                  />
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Recent Quotes */}
      {quotes.length > 0 && (
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <FileText className="h-5 w-5 text-primary-600" />
            Recent Quotes
          </h3>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {quotes.slice(0, 6).map((quote) => (
              <QuoteCard key={quote.id} quote={quote} lender={lenders.find((l) => l.id === quote.lender_id)} />
            ))}
          </div>
        </div>
      )}

      {/* Profile Modal */}
      {showProfileModal && (
        <Modal title="Borrower Profile" onClose={() => setShowProfileModal(false)}>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">Full Name</label>
                <input
                  type="text"
                  value={profileForm.full_name || ""}
                  onChange={(e) => setProfileForm({ ...profileForm, full_name: e.target.value })}
                  className="input w-full"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                <input
                  type="email"
                  value={profileForm.email || ""}
                  onChange={(e) => setProfileForm({ ...profileForm, email: e.target.value })}
                  className="input w-full"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Phone</label>
                <input
                  type="tel"
                  value={profileForm.phone || ""}
                  onChange={(e) => setProfileForm({ ...profileForm, phone: e.target.value })}
                  className="input w-full"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Credit Score</label>
                <input
                  type="number"
                  value={profileForm.credit_score || ""}
                  onChange={(e) => setProfileForm({ ...profileForm, credit_score: parseInt(e.target.value) || undefined })}
                  className="input w-full"
                  min={300}
                  max={850}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Annual Income</label>
                <input
                  type="number"
                  value={profileForm.annual_income || ""}
                  onChange={(e) => setProfileForm({ ...profileForm, annual_income: parseInt(e.target.value) || undefined })}
                  className="input w-full"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Total Assets</label>
                <input
                  type="number"
                  value={profileForm.total_assets || ""}
                  onChange={(e) => setProfileForm({ ...profileForm, total_assets: parseInt(e.target.value) || undefined })}
                  className="input w-full"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Properties Owned</label>
                <input
                  type="number"
                  value={profileForm.properties_owned ?? ""}
                  onChange={(e) => setProfileForm({ ...profileForm, properties_owned: parseInt(e.target.value) || 0 })}
                  className="input w-full"
                  min={0}
                />
              </div>
              <div className="col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">Investment Experience</label>
                <select
                  value={profileForm.investment_experience || ""}
                  onChange={(e) => setProfileForm({ ...profileForm, investment_experience: e.target.value })}
                  className="input w-full"
                >
                  <option value="">Select...</option>
                  <option value="beginner">Beginner (0-2 properties)</option>
                  <option value="intermediate">Intermediate (3-10 properties)</option>
                  <option value="experienced">Experienced (10+ properties)</option>
                </select>
              </div>
            </div>
            <div className="flex justify-end gap-2">
              <button onClick={() => setShowProfileModal(false)} className="btn-secondary">
                Cancel
              </button>
              <button onClick={handleSaveProfile} className="btn-primary">
                Save Profile
              </button>
            </div>
          </div>
        </Modal>
      )}

      {/* Lender Modal */}
      {showLenderModal && (
        <Modal
          title={editingLender ? "Edit Lender" : "Add Lender"}
          onClose={() => {
            setShowLenderModal(false);
            setEditingLender(null);
          }}
        >
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">Lender Name *</label>
                <input
                  type="text"
                  value={lenderForm.name || ""}
                  onChange={(e) => setLenderForm({ ...lenderForm, name: e.target.value })}
                  className="input w-full"
                  placeholder="ABC Bank"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Type</label>
                <select
                  value={lenderForm.lender_type || "bank"}
                  onChange={(e) => setLenderForm({ ...lenderForm, lender_type: e.target.value })}
                  className="input w-full"
                >
                  <option value="bank">Bank</option>
                  <option value="credit_union">Credit Union</option>
                  <option value="mortgage_broker">Mortgage Broker</option>
                  <option value="hard_money">Hard Money</option>
                  <option value="private">Private Lender</option>
                  <option value="dscr_lender">DSCR Lender</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Contact Name</label>
                <input
                  type="text"
                  value={lenderForm.contact_name || ""}
                  onChange={(e) => setLenderForm({ ...lenderForm, contact_name: e.target.value })}
                  className="input w-full"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                <input
                  type="email"
                  value={lenderForm.contact_email || ""}
                  onChange={(e) => setLenderForm({ ...lenderForm, contact_email: e.target.value })}
                  className="input w-full"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Phone</label>
                <input
                  type="tel"
                  value={lenderForm.contact_phone || ""}
                  onChange={(e) => setLenderForm({ ...lenderForm, contact_phone: e.target.value })}
                  className="input w-full"
                />
              </div>
              <div className="col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">Website</label>
                <input
                  type="url"
                  value={lenderForm.website || ""}
                  onChange={(e) => setLenderForm({ ...lenderForm, website: e.target.value })}
                  className="input w-full"
                  placeholder="https://..."
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Min Credit Score</label>
                <input
                  type="number"
                  value={lenderForm.min_credit_score || ""}
                  onChange={(e) => setLenderForm({ ...lenderForm, min_credit_score: parseInt(e.target.value) || undefined })}
                  className="input w-full"
                  min={300}
                  max={850}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Max LTV (%)</label>
                <input
                  type="number"
                  value={lenderForm.max_ltv || ""}
                  onChange={(e) => setLenderForm({ ...lenderForm, max_ltv: parseFloat(e.target.value) || undefined })}
                  className="input w-full"
                  min={0}
                  max={100}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Rate Low (%)</label>
                <input
                  type="number"
                  step="0.125"
                  value={lenderForm.rate_range_low || ""}
                  onChange={(e) => setLenderForm({ ...lenderForm, rate_range_low: parseFloat(e.target.value) || undefined })}
                  className="input w-full"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Rate High (%)</label>
                <input
                  type="number"
                  step="0.125"
                  value={lenderForm.rate_range_high || ""}
                  onChange={(e) => setLenderForm({ ...lenderForm, rate_range_high: parseFloat(e.target.value) || undefined })}
                  className="input w-full"
                />
              </div>
              <div className="col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">Notes</label>
                <textarea
                  value={lenderForm.notes || ""}
                  onChange={(e) => setLenderForm({ ...lenderForm, notes: e.target.value })}
                  className="input w-full"
                  rows={2}
                />
              </div>
              <div className="col-span-2">
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={lenderForm.is_active !== false}
                    onChange={(e) => setLenderForm({ ...lenderForm, is_active: e.target.checked })}
                    className="rounded border-gray-300"
                  />
                  <span className="text-sm text-gray-700">Active</span>
                </label>
              </div>
            </div>
            <div className="flex justify-end gap-2">
              <button
                onClick={() => {
                  setShowLenderModal(false);
                  setEditingLender(null);
                }}
                className="btn-secondary"
              >
                Cancel
              </button>
              <button onClick={handleSaveLender} disabled={!lenderForm.name} className="btn-primary">
                {editingLender ? "Update" : "Add"} Lender
              </button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
}
