/**
 * Base interface for API responses that include `id`, `createdAt`, and `updatedAt` fields.
 */
export interface BaseEntity {
  id: string;
  createdAt: string;
  updatedAt: string;
}
