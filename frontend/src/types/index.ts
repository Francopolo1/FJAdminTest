export type UserRole =
  | "admin"
  | "director_manager"
  | "supervisor"
  | "inspector"
  | "it_staff"
  | "support_staff"
  | "readonly";

export interface AuthUser {
  id: number;
  username: string;
  first_name: string;
  last_name: string;
  email: string;
  full_name: string;
  is_staff: boolean;
  is_active: boolean;
  is_inspector: boolean;
  role: UserRole;
  date_joined: string;
}

export interface InspectorProgram {
  program_id: string;
  code: string;
  title: string;
}

export interface InspectorProgramDistrict {
  program_district_id: string;
  program_code: string;
  program_title: string;
  district: number | null;
  description: string | null;
}

export interface InspectorProgramFacility {
  program_facility_id: string;
  facility_id: string;
  facility_name: string | null;
  program_district_id: string;
  program_code: string;
  district: number | null;
  facility_type: string | null;
  license_number: string | null;
  risk_assessment: string | null;
  activity_flag: string | null;
  last_visit_date: string | null;
  next_visit_date: string | null;
}

export interface InspectorLanding {
  programs: InspectorProgram[];
  program_districts: InspectorProgramDistrict[];
  program_facilities: InspectorProgramFacility[];
}

export interface SupervisorDirectReport {
  user_id: number;
  full_name: string;
  email: string;
  job_title: string | null;
  department: string | null;
  role: string | null;
  is_active: boolean;
  assigned_programs: InspectorProgram[];
}

export interface SupervisorLanding {
  assigned_programs: InspectorProgram[];
  direct_reports: SupervisorDirectReport[];
}

export interface WorkflowInstanceSummary {
  instance_id: string;
  reference_no: string;
  workflow_name: string;
  initiated_by_name: string;
  current_step_name: string | null;
  status: string;
  priority: number;
  started_at: string;
  due_date: string | null;
}

export interface ActivityWorkflowOption {
  workflow_id: string;
  name: string;
  category: string | null;
}

export interface ProgramFacilityTypeActivity {
  program_facility_type_activity_id: string;
  description: string;
  specialtracking: string | null;
  workflows: ActivityWorkflowOption[];
}

export interface InspectorFacilityAssignment {
  program_facility_id: string;
  program_code: string;
  district: number | null;
  facility_type: string | null;
  profile: string | null;
  license_number: string | null;
  risk_assessment: string | null;
  activity_flag: string | null;
  last_visit_date: string | null;
  next_visit_date: string | null;
  instances: WorkflowInstanceSummary[];
  activities: ProgramFacilityTypeActivity[];
}

export interface InspectorFacilityLocation {
  address_line1: string | null;
  address_line2: string | null;
  city: string | null;
  state: string | null;
  postal_code: string | null;
  city_state_zip: string | null;
  latitude: number | null;
  longitude: number | null;
}

export interface InspectorFacilityDetail {
  facility_id: string;
  facility_name: string | null;
  location: InspectorFacilityLocation | null;
  assignments: InspectorFacilityAssignment[];
}

// ── Facility directory ────────────────────────────────────────────────

export interface FacilityListItem {
  facility_id: string;
  facility_name: string | null;
  program_facility_id: string;
  program_id: string;
  program_code: string;
  facility_type_id: string | null;
  facility_type: string | null;
  district: number | null;
  city: string | null;
  state: string | null;
  license_number: string | null;
  activity_flag: string | null;
}

export interface FacilityProgramOption {
  program_id: string;
  code: string;
  title: string;
}

export interface FacilityTypeOption {
  facility_type_id: string;
  code: string;
  description: string | null;
}

export interface FacilityFilterOptions {
  programs: FacilityProgramOption[];
  facility_types: FacilityTypeOption[];
}

export interface FacilityAssignmentSummary {
  program_facility_id: string;
  program_code: string;
  district: number | null;
  facility_type: string | null;
  profile: string | null;
  license_number: string | null;
  risk_assessment: string | null;
  activity_flag: string | null;
  last_visit_date: string | null;
  next_visit_date: string | null;
  instances: WorkflowInstanceSummary[];
  activities: ProgramFacilityTypeActivity[];
}

export interface FacilityDetail {
  facility_id: string;
  facility_name: string | null;
  location: InspectorFacilityLocation | null;
  assignments: FacilityAssignmentSummary[];
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface TokenPair {
  access: string;
  refresh: string;
}

export interface RegisterPayload {
  first_name: string;
  last_name: string;
  email: string;
  password: string;
}

export interface RegisterResponse {
  access?: string;
  refresh?: string;
  user?: AuthUser;
  detail?: string;
}

export interface Paginated<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface WorkflowTask {
  task_id: string;
  instance: string;
  step: string;
  step_name: string;
  status: string;
  comments: string | null;
  assigned_to: number | null;
  assigned_to_name: string | null;
  assigned_by: number | null;
  assigned_at: string;
  due_date: string | null;
  completed_at: string | null;
  hours_remaining: number | null;
}

export interface WorkflowInstance {
  instance_id: string;
  workflow: string;
  workflow_name: string;
  initiated_by: number;
  initiated_by_name: string;
  current_step: string | null;
  current_step_name: string | null;
  status: string;
  reference_no: string;
  priority: number;
  started_at: string;
  completed_at: string | null;
  due_date: string | null;
  program_facility: string | null;
  program_title?: string | null;
  activity?: string | null;
}

export interface WorkflowInstanceDetail extends WorkflowInstance {
  request_data: unknown;
  tasks: WorkflowTask[];
}

export interface AuditLogEntry {
  log_id: string;
  instance: string;
  task: string | null;
  actor: number | null;
  actor_name: string | null;
  action: string;
  from_status: string | null;
  to_status: string | null;
  notes: string | null;
  logged_at: string;
}

export interface AvailableTransition {
  trigger_event: string;
  transition_name: string;
  to_step__step_name: string;
}

export interface StatusDistribution {
  status: string;
  count: number;
}

export interface ProgramDistributionItem {
  program_code: string | null;
  program_title: string | null;
  count: number;
}

export interface ActivityDistributionItem {
  activity: string | null;
  count: number;
}

export interface InstanceDistributions {
  by_program: ProgramDistributionItem[];
  by_activity: ActivityDistributionItem[];
}

export interface DashboardStats {
  instances: {
    total: number;
    in_progress: number;
    approved: number;
  };
  tasks: {
    total: number;
    overdue: number;
  };
  status_dist: StatusDistribution[];
  timestamp: string;
}

// ── Checklists ─────────────────────────────────────────────────────────

export interface ChecklistRunListItem {
  run_id: string;
  instance: string;
  reference_no: string;
  workflow_name: string;
  task: string | null;
  template: string;
  template_title: string;
  blocks_advance: boolean;
  status: string;
  total_items: number;
  total_required: number;
  answered_items: number;
  answered_required: number;
  completion_pct: number;
  required_completion_pct: number;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
}

export interface ChecklistResponseItem {
  response_id: string;
  run: string;
  item: string;
  item_text: string;
  response_type: string;
  is_required: boolean;
  responded_by: number | null;
  responded_by_name: string | null;
  response_value: string | null;
  notes: string | null;
  box_folder_url: string | null;
  responded_at: string | null;
}

export interface ChecklistRunDetail extends ChecklistRunListItem {
  template_description: string | null;
  is_blocking: boolean;
  responses: ChecklistResponseItem[];
}

export interface ChecklistItemComplianceRuleRef {
  checklist_item_compliance_rule_id: string;
  rule_code: string;
  rule_name: string;
}

export interface ChecklistProgressItem {
  item_id: string;
  item_text: string;
  help_text: string | null;
  response_type: string;
  category: string | null;
  is_required: boolean;
  options: string[] | null;
  default_value: string | null;
  example_url: string | null;
  answered: boolean;
  response_id: string | null;
  response_value: string | null;
  notes: string | null;
  box_folder_url: string | null;
  responded_by: string | null;
  responded_at: string | null;
  compliance_rules: ChecklistItemComplianceRuleRef[];
}

export interface ChecklistProgress {
  run_id: string;
  status: string;
  blocks_advance: boolean;
  completion_pct: number;
  required_completion_pct: number;
  total_items: number;
  answered_items: number;
  total_required: number;
  answered_required: number;
  items: ChecklistProgressItem[];
  violations: ComplianceViolation[];
}

// ── Compliance ─────────────────────────────────────────────────────────

export interface ComplianceViolation {
  compliance_violation_id: string;
  checklist_item_compliance_rule: string;
  rule_code: string;
  rule_name: string;
  item_text: string | null;
  violation_date: string;
  violation_severity_level: string;
  severity_name: string;
  severity_code: string;
  violation_description: string | null;
  detected_by: number;
  checklist_response: string;
}

export interface ViolationSeverityLevel {
  violation_severity_level_id: string;
  code: string;
  name: string;
  rank: number;
}

export interface ComplianceSummary {
  total_rules: number;
  active_rules: number;
  total_violations: number;
  violations_last_30_days: number;
  rules_with_violations: number;
  top_violated_rules: { compliance_rule__code: string; compliance_rule__name: string; count: number }[];
  severity_breakdown: { violation_severity_level__code: string; violation_severity_level__name: string; count: number }[];
  active_fine_schedules: number;
}

// ── Financials ─────────────────────────────────────────────────────────

export interface Transaction {
  id: number;
  transaction_date: string;
  reference_number: string;
  description: string;
  amount: string;
  currency: string;
  status: string;
  foapal_code: string | null;
  fund_code: string | null;
  org_code: string | null;
  account_code: string | null;
  source_system: string | null;
  coded_by: string | null;
  approved_by: string | null;
}

export interface FinancialsSummary {
  total_transactions: number;
  total_amount: string;
  pending_count: number;
  pending_amount: string;
  approved_count: number;
  approved_amount: string;
  posted_count: number;
  posted_amount: string;
  voided_count: number;
  status_breakdown: { status: string; count: number; total: string }[];
  top_funds: { fund__code: string; fund__title: string; count: number; total: string }[];
  top_accounts: { account__code: string; account__title: string; account__account_type: string; count: number; total: string }[];
  active_foapal_strings: number;
  total_splits: number;
}
