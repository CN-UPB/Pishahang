/** Son-Mano Framework Plugins Modal */

export enum PluginState {
  RUNNING = "RUNNING",
  PAUSED = "PAUSED",
}

export interface Plugin {
  description: string;
  id: string;
  lastHeartbeatAt: string;
  name: string;
  registeredAt: string;
  state: PluginState;
  version: string;
}
