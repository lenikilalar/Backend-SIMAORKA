# SIMAORKA Database Schema

Overview of the database tables and their relationships in the SIMAORKA Backend.

## 1. Identity & Profiles

### `users`
Core user table extending Django AbstractBaseUser.
| Field | Type | Modifiers | Description |
| :--- | :--- | :--- | :--- |
| `id` | UUID | PK | |
| `email` | String | Unique | Login email |
| `google_sub` | String | Unique, Nullable | Google OAuth ID |
| `is_staff` | Boolean | | Org Admin access flag |
| `is_superuser` | Boolean | | System Superadmin flag |
| `is_active` | Boolean | Default True | Access control |

### `student_profiles`
Extended profile for students. One-to-One with `users`.
| Field | Type | Modifiers | Description |
| :--- | :--- | :--- | :--- |
| `user_id` | UUID | PK, FK | Link to User |
| `nim` | String | Unique | Student ID Number |
| `full_name` | String | | |
| `faculty` | String | | |
| `major` | String | | |
| `entry_year` | Integer | | |
| `profile_photo_url` | Text | Nullable | |
| `bio` | Text | Nullable | |

### `email_preferences`
User notification settings. One-to-One with `users`.
| Field | Type | Modifiers | Description |
| :--- | :--- | :--- | :--- |
| `user_id` | UUID | PK, FK | |
| `receive_announcements` | Boolean | | |
| `receive_events` | Boolean | | |
| `digest_frequency` | Enum | | 'instant', 'daily', 'weekly' |

## 2. Organizations & Members

### `organizations`
Student organizations (BEM, Hima, UKM).
| Field | Type | Modifiers | Description |
| :--- | :--- | :--- | :--- |
| `id` | UUID | PK | |
| `slug` | Slug | Unique | URL identifier |
| `name` | String | | |
| `status` | Enum | | 'draft', 'active', 'suspended' |
| `is_private` | Boolean | | Hidden from public list |
| `finance_transparency` | Enum | | 'private', 'summary', 'full' |
| `created_by` | UUID | FK | Creator user |

### `organization_members`
Junction table for User-Organization membership.
| Field | Type | Modifiers | Description |
| :--- | :--- | :--- | :--- |
| `id` | UUID | PK | |
| `organization_id` | UUID | FK | |
| `user_id` | UUID | FK | |
| `status` | Enum | | 'pending', 'active', 'rejected' |
| `joined_at` | DateTime | | |

### `organization_positions`
Structural positions (Ketua, Bendahara).
| Field | Type | Modifiers | Description |
| :--- | :--- | :--- | :--- |
| `organization_id` | UUID | FK | |
| `name` | String | | Position title |
| `rank` | Integer | | Sorting order |

### `member_positions`
Assigns a member to a structural position.
| Field | Type | Modifiers | Description |
| :--- | :--- | :--- | :--- |
| `member_id` | UUID | FK | |
| `position_id` | UUID | FK | |
| `start_at` | DateTime | | Tenure start |
| `end_at` | DateTime | | Tenure end |

### `org_periods`
Management periods (e.g., "2024/2025").
| Field | Type | Modifiers | Description |
| :--- | :--- | :--- | :--- |
| `organization_id` | UUID | FK | |
| `name` | String | | Period Name |
| `start_date` | Date | | |
| `end_date` | Date | | |
| `is_active` | Boolean | | Current active period |

### `organization_requests`
Requests to create new organizations.
| Field | Type | Modifiers | Description |
| :--- | :--- | :--- | :--- |
| `proposed_name` | String | | |
| `requester_user_id` | UUID | FK | |
| `status` | Enum | | 'submitted', 'approved', 'rejected' |
| `handled_by` | UUID | FK | Admin who reviewed |

## 3. RBAC (Access Control)

### `roles`
Defined roles (e.g., "SYSTEM_ADMIN", "ORG_MEMBER").
| Field | Type | Modifiers | Description |
| :--- | :--- | :--- | :--- |
| `code` | String | Unique | e.g. "TREASURER" |
| `name` | String | | Readable name |
| `scope` | Enum | | 'SYSTEM' or 'ORG' |

### `permissions`
Granular permissions (e.g., "FINANCE_VIEW", "EVENT_CREATE").
| Field | Type | Modifiers | Description |
| :--- | :--- | :--- | :--- |
| `code` | String | Unique | |

### `role_permissions`
Mapping of Roles to Permissions (Many-to-Many).
| Field | Type | Modifiers | Description |
| :--- | :--- | :--- | :--- |
| `role_id` | ID | FK | |
| `permission_id` | ID | FK | |

### `member_roles`
Assigns RBAC roles to Organization Members.
| Field | Type | Modifiers | Description |
| :--- | :--- | :--- | :--- |
| `member_id` | UUID | FK | |
| `role_id` | ID | FK | |

## 4. Web3 & Blockchain

### `user_wallets`
Users' connected crypto wallets.
| Field | Type | Modifiers | Description |
| :--- | :--- | :--- | :--- |
| `user_id` | UUID | FK | |
| `wallet_address` | String | | 0x... |
| `chain` | Enum | | 'ethereum', 'sepolia', etc. |
| `is_verified` | Boolean | | SIWE verification status |

### `web3_contracts`
Smart contracts deployed by organizations.
| Field | Type | Modifiers | Description |
| :--- | :--- | :--- | :--- |
| `organization_id` | UUID | FK | |
| `address` | String | Unique | Contract Address |
| `contract_type` | Enum | | 'role_nft', 'gov_token', 'dues' |
| `abi` | JSON | | Contract Interface |

### `org_roles_catalog`
Catalog of on-chain Roles (NFT types).
| Field | Type | Modifiers | Description |
| :--- | :--- | :--- | :--- |
| `organization_id` | UUID | FK | |
| `role_code` | String | | e.g. "TREASURER_NFT" |

### `org_role_assignments`
Minted Role NFTs assigned to wallets.
| Field | Type | Modifiers | Description |
| :--- | :--- | :--- | :--- |
| `organization_id` | UUID | FK | |
| `role_id` | UUID | FK | Link to Catalog |
| `wallet_address` | String | | Owner |
| `token_id` | BigInt | | NFT ID |
| `tx_hash` | String | | Minting Transaction |
| `period_id` | UUID | FK | Associated Period |

## 5. Finance

### `finance_ledgers`
Financial books for organizations.
| Field | Type | Modifiers | Description |
| :--- | :--- | :--- | :--- |
| `organization_id` | UUID | FK | |
| `name` | String | | e.g. "Main Cash" |
| `currency` | String | | Default 'IDR' |

### `finance_transactions`
Income/Expense records.
| Field | Type | Modifiers | Description |
| :--- | :--- | :--- | :--- |
| `ledger_id` | UUID | FK | |
| `type` | Enum | | 'income', 'expense' |
| `amount` | Decimal | | |
| `visibility` | Enum | | 'members_only', 'public_summary' |
| `source` | Enum | | 'manual', 'web3' |

### `web3_payments`
Blockchain payment details for transactions.
| Field | Type | Modifiers | Description |
| :--- | :--- | :--- | :--- |
| `transaction_id` | UUID | FK | One-to-One |
| `tx_hash` | String | Unique | |
| `amount_wei` | String | | Exact amount on-chain |
| `status` | Enum | | 'pending', 'confirmed' |

## 6. Voting

### `votes`
Voting sessions.
| Field | Type | Modifiers | Description |
| :--- | :--- | :--- | :--- |
| `organization_id` | UUID | FK | |
| `title` | String | | |
| `type` | Enum | | 'simple', 'token_weighted' |
| `options` | JSON | | List of candidates/options |
| `snapshot_block` | Integer | | For token-weighted |

### `vote_casts`
Individual votes.
| Field | Type | Modifiers | Description |
| :--- | :--- | :--- | :--- |
| `vote_id` | UUID | FK | |
| `wallet_address` | String | | Distinct per vote |
| `option_index` | Integer | | Selected option |
| `weight` | Decimal | | Default 1 or Token Balance |

## 7. Content & Events

### `announcements`
Organization announcements.
| Field | Type | Modifiers | Description |
| :--- | :--- | :--- | :--- |
| `organization_id` | UUID | FK | |
| `title` | String | | |
| `pinned` | Boolean | | |

### `events`
| Field | Type | Modifiers | Description |
| :--- | :--- | :--- | :--- |
| `organization_id` | UUID | FK | |
| `start_at` | DateTime | | |
| `end_at` | DateTime | | |
| `location` | Text | | |

### `event_attendance`
RSVP list.
| Field | Type | Modifiers | Description |
| :--- | :--- | :--- | :--- |
| `event_id` | UUID | FK | |
| `user_id` | UUID | FK | |
| `status` | Enum | | 'going', 'interested' |

## 8. Documents

### `documents`
File registry.
| Field | Type | Modifiers | Description |
| :--- | :--- | :--- | :--- |
| `organization_id` | UUID | FK | |
| `title` | String | | |
| `requires_nft` | Boolean | | Web3 Gating |

### `document_versions`
Version control for files.
| Field | Type | Modifiers | Description |
| :--- | :--- | :--- | :--- |
| `document_id` | UUID | FK | |
| `version_number` | Integer | | |
| `file_path` | Text | | S3/Local path |
| `file_hash` | String | | SHA256 integrity |

## 9. Communication

### `discussion_threads`
Forums/Threads within orgs.
| Field | Type | Modifiers | Description |
| :--- | :--- | :--- | :--- |
| `organization_id` | UUID | FK | |
| `title` | String | | |
| `lock_status` | Enum | | 'open', 'locked' |

### `chat_threads` (Direct & Groups)
### `chat_messages`

## 10. Audit & Notifications

### `audit_logs`
Security trail.
| Field | Type | Modifiers | Description |
| :--- | :--- | :--- | :--- |
| `user_id` | UUID | FK | Actor |
| `action` | String | | What happened |
| `ip_address` | String | | |

### `notifications`
In-app alerts.
