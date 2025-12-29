"use client";

/**
 * ContactsPanel Component
 *
 * Shows contacts and communication timeline for a property.
 * Allows adding new contacts, logging communications, and generating emails.
 */

import { useState, useEffect } from "react";
import {
  Users,
  Plus,
  Phone,
  Mail,
  Building2,
  MessageSquare,
  Calendar,
  ChevronDown,
  ChevronUp,
  Loader2,
  Trash2,
  Edit3,
  Copy,
  CheckCircle,
  Clock,
  FileText,
  X,
} from "lucide-react";
import {
  api,
  Contact,
  Communication,
  EmailTemplate,
  GeneratedEmail,
} from "@/lib/api";
import { cn } from "@/lib/utils";

interface ContactsPanelProps {
  propertyId: string;
  propertyAddress?: string;
  propertyCity?: string;
  listPrice?: number;
}

export function ContactsPanel({
  propertyId,
  propertyAddress,
  propertyCity,
  listPrice,
}: ContactsPanelProps) {
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [communications, setCommunications] = useState<Communication[]>([]);
  const [templates, setTemplates] = useState<EmailTemplate[]>([]);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState(true);

  // Modal states
  const [showAddContact, setShowAddContact] = useState(false);
  const [showLogComm, setShowLogComm] = useState(false);
  const [showEmailGenerator, setShowEmailGenerator] = useState(false);
  const [selectedContact, setSelectedContact] = useState<Contact | null>(null);

  // Form states
  const [newContact, setNewContact] = useState({
    name: "",
    email: "",
    phone: "",
    company: "",
    contact_type: "listing_agent",
    notes: "",
  });
  const [newComm, setNewComm] = useState({
    comm_type: "email",
    direction: "outbound",
    subject: "",
    content: "",
  });

  // Fetch data
  useEffect(() => {
    async function fetchData() {
      try {
        setLoading(true);
        const [contactsData, commsData, templatesData] = await Promise.all([
          api.getContacts({ property_id: propertyId }),
          api.getCommunications({ property_id: propertyId }),
          api.getEmailTemplates(),
        ]);
        setContacts(contactsData);
        setCommunications(commsData);
        setTemplates(templatesData);
      } catch (err) {
        console.error("Failed to fetch contacts data:", err);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, [propertyId]);

  // Add contact
  const handleAddContact = async () => {
    try {
      const contact = await api.createContact({
        ...newContact,
        property_ids: [propertyId],
      });
      setContacts([contact, ...contacts]);
      setShowAddContact(false);
      setNewContact({
        name: "",
        email: "",
        phone: "",
        company: "",
        contact_type: "listing_agent",
        notes: "",
      });
    } catch (err) {
      console.error("Failed to add contact:", err);
    }
  };

  // Log communication
  const handleLogComm = async () => {
    if (!selectedContact) return;
    try {
      const comm = await api.createCommunication({
        contact_id: selectedContact.id,
        property_id: propertyId,
        ...newComm,
      });
      setCommunications([comm, ...communications]);
      setShowLogComm(false);
      setNewComm({
        comm_type: "email",
        direction: "outbound",
        subject: "",
        content: "",
      });
      setSelectedContact(null);
    } catch (err) {
      console.error("Failed to log communication:", err);
    }
  };

  // Delete contact
  const handleDeleteContact = async (contact: Contact) => {
    if (!confirm(`Delete ${contact.name}?`)) return;
    try {
      await api.deleteContact(contact.id);
      setContacts(contacts.filter((c) => c.id !== contact.id));
    } catch (err) {
      console.error("Failed to delete contact:", err);
    }
  };

  const contactTypeLabels: Record<string, string> = {
    listing_agent: "Listing Agent",
    buyer_agent: "Buyer Agent",
    seller: "Seller",
    lender: "Lender",
    other: "Other",
  };

  const commTypeLabels: Record<string, string> = {
    email: "Email",
    call: "Call",
    text: "Text",
    meeting: "Meeting",
    note: "Note",
  };

  return (
    <div className="card">
      {/* Header */}
      <div
        className="flex items-center justify-between cursor-pointer"
        onClick={() => setExpanded(!expanded)}
      >
        <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
          <Users className="h-5 w-5 text-primary-600" />
          Contacts & Outreach
          {contacts.length > 0 && (
            <span className="ml-2 px-2 py-0.5 bg-primary-100 text-primary-700 rounded-full text-sm">
              {contacts.length}
            </span>
          )}
        </h3>
        <div className="flex items-center gap-2">
          {!loading && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                setShowAddContact(true);
              }}
              className="btn-secondary text-sm px-2 py-1"
            >
              <Plus className="h-4 w-4" />
            </button>
          )}
          {expanded ? (
            <ChevronUp className="h-5 w-5 text-gray-400" />
          ) : (
            <ChevronDown className="h-5 w-5 text-gray-400" />
          )}
        </div>
      </div>

      {expanded && (
        <div className="mt-4">
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin text-primary-500" />
            </div>
          ) : (
            <>
              {/* Contacts List */}
              {contacts.length === 0 ? (
                <div className="text-center py-6 text-gray-500">
                  <Users className="h-8 w-8 mx-auto mb-2 opacity-50" />
                  <p>No contacts yet</p>
                  <button
                    onClick={() => setShowAddContact(true)}
                    className="mt-2 text-primary-600 hover:text-primary-700 text-sm"
                  >
                    Add a contact
                  </button>
                </div>
              ) : (
                <div className="space-y-3">
                  {contacts.map((contact) => (
                    <div
                      key={contact.id}
                      className="border rounded-lg p-3 hover:bg-gray-50"
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex items-center gap-3">
                          {contact.agent_photo_url ? (
                            <img
                              src={contact.agent_photo_url}
                              alt={contact.name}
                              className="h-10 w-10 rounded-full object-cover"
                            />
                          ) : (
                            <div className="h-10 w-10 rounded-full bg-gray-200 flex items-center justify-center">
                              <Users className="h-5 w-5 text-gray-500" />
                            </div>
                          )}
                          <div>
                            <p className="font-medium text-gray-900">
                              {contact.name}
                            </p>
                            <p className="text-sm text-gray-500">
                              {contactTypeLabels[contact.contact_type || "other"]}
                              {contact.company && ` at ${contact.company}`}
                            </p>
                          </div>
                        </div>
                        <div className="flex items-center gap-1">
                          <button
                            onClick={() => {
                              setSelectedContact(contact);
                              setShowEmailGenerator(true);
                            }}
                            className="p-1 text-gray-400 hover:text-primary-600"
                            title="Generate email"
                          >
                            <Mail className="h-4 w-4" />
                          </button>
                          <button
                            onClick={() => {
                              setSelectedContact(contact);
                              setShowLogComm(true);
                            }}
                            className="p-1 text-gray-400 hover:text-primary-600"
                            title="Log communication"
                          >
                            <MessageSquare className="h-4 w-4" />
                          </button>
                          <button
                            onClick={() => handleDeleteContact(contact)}
                            className="p-1 text-gray-400 hover:text-red-600"
                            title="Delete contact"
                          >
                            <Trash2 className="h-4 w-4" />
                          </button>
                        </div>
                      </div>

                      {/* Contact details */}
                      <div className="mt-2 flex flex-wrap gap-3 text-sm">
                        {contact.email && (
                          <a
                            href={`mailto:${contact.email}`}
                            className="flex items-center gap-1 text-gray-600 hover:text-primary-600"
                          >
                            <Mail className="h-3 w-3" />
                            {contact.email}
                          </a>
                        )}
                        {contact.phone && (
                          <a
                            href={`tel:${contact.phone}`}
                            className="flex items-center gap-1 text-gray-600 hover:text-primary-600"
                          >
                            <Phone className="h-3 w-3" />
                            {contact.phone}
                          </a>
                        )}
                      </div>

                      {/* Last contacted */}
                      {contact.last_contacted && (
                        <p className="mt-2 text-xs text-gray-400">
                          Last contacted:{" "}
                          {new Date(contact.last_contacted).toLocaleDateString()}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              )}

              {/* Communication Timeline */}
              {communications.length > 0 && (
                <div className="mt-4 pt-4 border-t">
                  <h4 className="text-sm font-medium text-gray-700 mb-3 flex items-center gap-2">
                    <Clock className="h-4 w-4" />
                    Recent Activity
                  </h4>
                  <div className="space-y-2">
                    {communications.slice(0, 5).map((comm) => {
                      const contact = contacts.find(
                        (c) => c.id === comm.contact_id
                      );
                      return (
                        <div
                          key={comm.id}
                          className="flex items-start gap-2 text-sm"
                        >
                          <div
                            className={cn(
                              "mt-1 h-2 w-2 rounded-full",
                              comm.direction === "outbound"
                                ? "bg-blue-500"
                                : "bg-green-500"
                            )}
                          />
                          <div>
                            <span className="font-medium">
                              {commTypeLabels[comm.comm_type]}
                            </span>
                            {contact && (
                              <span className="text-gray-500">
                                {" "}
                                with {contact.name}
                              </span>
                            )}
                            {comm.subject && (
                              <span className="text-gray-500">
                                : {comm.subject}
                              </span>
                            )}
                            <span className="text-gray-400 ml-2 text-xs">
                              {new Date(comm.occurred_at).toLocaleDateString()}
                            </span>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      )}

      {/* Add Contact Modal */}
      {showAddContact && (
        <Modal
          title="Add Contact"
          onClose={() => setShowAddContact(false)}
        >
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Name *
              </label>
              <input
                type="text"
                value={newContact.name}
                onChange={(e) =>
                  setNewContact({ ...newContact, name: e.target.value })
                }
                className="input w-full"
                placeholder="John Smith"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Type
              </label>
              <select
                value={newContact.contact_type}
                onChange={(e) =>
                  setNewContact({ ...newContact, contact_type: e.target.value })
                }
                className="input w-full"
              >
                {Object.entries(contactTypeLabels).map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </select>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Email
                </label>
                <input
                  type="email"
                  value={newContact.email}
                  onChange={(e) =>
                    setNewContact({ ...newContact, email: e.target.value })
                  }
                  className="input w-full"
                  placeholder="john@example.com"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Phone
                </label>
                <input
                  type="tel"
                  value={newContact.phone}
                  onChange={(e) =>
                    setNewContact({ ...newContact, phone: e.target.value })
                  }
                  className="input w-full"
                  placeholder="(555) 123-4567"
                />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Company
              </label>
              <input
                type="text"
                value={newContact.company}
                onChange={(e) =>
                  setNewContact({ ...newContact, company: e.target.value })
                }
                className="input w-full"
                placeholder="ABC Realty"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Notes
              </label>
              <textarea
                value={newContact.notes}
                onChange={(e) =>
                  setNewContact({ ...newContact, notes: e.target.value })
                }
                className="input w-full"
                rows={2}
              />
            </div>
            <div className="flex justify-end gap-2">
              <button
                onClick={() => setShowAddContact(false)}
                className="btn-secondary"
              >
                Cancel
              </button>
              <button
                onClick={handleAddContact}
                disabled={!newContact.name}
                className="btn-primary"
              >
                Add Contact
              </button>
            </div>
          </div>
        </Modal>
      )}

      {/* Log Communication Modal */}
      {showLogComm && selectedContact && (
        <Modal
          title={`Log Communication with ${selectedContact.name}`}
          onClose={() => {
            setShowLogComm(false);
            setSelectedContact(null);
          }}
        >
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Type
                </label>
                <select
                  value={newComm.comm_type}
                  onChange={(e) =>
                    setNewComm({ ...newComm, comm_type: e.target.value })
                  }
                  className="input w-full"
                >
                  {Object.entries(commTypeLabels).map(([value, label]) => (
                    <option key={value} value={value}>
                      {label}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Direction
                </label>
                <select
                  value={newComm.direction}
                  onChange={(e) =>
                    setNewComm({ ...newComm, direction: e.target.value })
                  }
                  className="input w-full"
                >
                  <option value="outbound">Outbound</option>
                  <option value="inbound">Inbound</option>
                  <option value="internal">Internal Note</option>
                </select>
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Subject
              </label>
              <input
                type="text"
                value={newComm.subject}
                onChange={(e) =>
                  setNewComm({ ...newComm, subject: e.target.value })
                }
                className="input w-full"
                placeholder="Initial inquiry about property"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Content / Notes
              </label>
              <textarea
                value={newComm.content}
                onChange={(e) =>
                  setNewComm({ ...newComm, content: e.target.value })
                }
                className="input w-full"
                rows={4}
                placeholder="Summary of the conversation..."
              />
            </div>
            <div className="flex justify-end gap-2">
              <button
                onClick={() => {
                  setShowLogComm(false);
                  setSelectedContact(null);
                }}
                className="btn-secondary"
              >
                Cancel
              </button>
              <button onClick={handleLogComm} className="btn-primary">
                Log Communication
              </button>
            </div>
          </div>
        </Modal>
      )}

      {/* Email Generator Modal */}
      {showEmailGenerator && selectedContact && (
        <EmailGeneratorModal
          contact={selectedContact}
          templates={templates}
          propertyAddress={propertyAddress}
          propertyCity={propertyCity}
          listPrice={listPrice}
          onClose={() => {
            setShowEmailGenerator(false);
            setSelectedContact(null);
          }}
          onLogEmail={(subject, body) => {
            // Log the email as a communication
            api.createCommunication({
              contact_id: selectedContact.id,
              property_id: propertyId,
              comm_type: "email",
              direction: "outbound",
              subject,
              content: body,
            }).then((comm) => {
              setCommunications([comm, ...communications]);
            });
          }}
        />
      )}
    </div>
  );
}

// Simple Modal Component
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
            <X className="h-5 w-5" />
          </button>
        </div>
        <div className="p-4">{children}</div>
      </div>
    </div>
  );
}

// Email Generator Component
function EmailGeneratorModal({
  contact,
  templates,
  propertyAddress,
  propertyCity,
  listPrice,
  onClose,
  onLogEmail,
}: {
  contact: Contact;
  templates: EmailTemplate[];
  propertyAddress?: string;
  propertyCity?: string;
  listPrice?: number;
  onClose: () => void;
  onLogEmail: (subject: string, body: string) => void;
}) {
  const [selectedTemplate, setSelectedTemplate] = useState<string>("");
  const [generatedEmail, setGeneratedEmail] = useState<GeneratedEmail | null>(null);
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);

  const handleGenerate = async () => {
    if (!selectedTemplate) return;
    setLoading(true);
    try {
      const email = await api.generateEmail(selectedTemplate, {
        agent_name: contact.name.split(" ")[0], // First name
        address: propertyAddress || "[Address]",
        city: propertyCity || "[City]",
        list_price: listPrice ? `$${listPrice.toLocaleString()}` : "[Price]",
        sender_name: "[Your Name]",
        sender_email: "[Your Email]",
        sender_phone: "[Your Phone]",
      });
      setGeneratedEmail(email);
    } catch (err) {
      console.error("Failed to generate email:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = () => {
    if (!generatedEmail) return;
    const text = `Subject: ${generatedEmail.subject}\n\n${generatedEmail.body}`;
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleSendAndLog = () => {
    if (!generatedEmail || !contact.email) return;
    // Open email client
    const mailtoUrl = `mailto:${contact.email}?subject=${encodeURIComponent(
      generatedEmail.subject
    )}&body=${encodeURIComponent(generatedEmail.body)}`;
    window.open(mailtoUrl, "_blank");
    // Log the email
    onLogEmail(generatedEmail.subject, generatedEmail.body);
    onClose();
  };

  return (
    <Modal title="Generate Email" onClose={onClose}>
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Template
          </label>
          <select
            value={selectedTemplate}
            onChange={(e) => setSelectedTemplate(e.target.value)}
            className="input w-full"
          >
            <option value="">Select a template...</option>
            {templates.map((t) => (
              <option key={t.id} value={t.id}>
                {t.name}
              </option>
            ))}
          </select>
          {selectedTemplate && (
            <p className="mt-1 text-xs text-gray-500">
              {templates.find((t) => t.id === selectedTemplate)?.description}
            </p>
          )}
        </div>

        {!generatedEmail && (
          <div className="flex justify-end">
            <button
              onClick={handleGenerate}
              disabled={!selectedTemplate || loading}
              className="btn-primary"
            >
              {loading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                "Generate Email"
              )}
            </button>
          </div>
        )}

        {generatedEmail && (
          <>
            <div className="border rounded-lg p-4 bg-gray-50">
              <p className="text-sm font-medium text-gray-700 mb-2">
                Subject: {generatedEmail.subject}
              </p>
              <pre className="text-sm text-gray-600 whitespace-pre-wrap font-sans">
                {generatedEmail.body}
              </pre>
            </div>

            <div className="flex items-center justify-between">
              <button
                onClick={() => setGeneratedEmail(null)}
                className="text-sm text-gray-500 hover:text-gray-700"
              >
                Generate different email
              </button>
              <div className="flex gap-2">
                <button
                  onClick={handleCopy}
                  className="btn-secondary flex items-center gap-1"
                >
                  {copied ? (
                    <>
                      <CheckCircle className="h-4 w-4 text-green-500" />
                      Copied!
                    </>
                  ) : (
                    <>
                      <Copy className="h-4 w-4" />
                      Copy
                    </>
                  )}
                </button>
                {contact.email && (
                  <button
                    onClick={handleSendAndLog}
                    className="btn-primary flex items-center gap-1"
                  >
                    <Mail className="h-4 w-4" />
                    Open in Email & Log
                  </button>
                )}
              </div>
            </div>
          </>
        )}
      </div>
    </Modal>
  );
}
