/**
 * Base interface for API response types that define `id`, `createdAt`, and `updatedAt` fields.
 */
export interface BaseEntity {
  id: string;
  createdAt: string;
  updatedAt: string;
}
