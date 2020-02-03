export interface ApiReply<P = any> {
  success: boolean;
  message?: string;
  payload?: P;
}
