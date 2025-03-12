import { Api } from './api';
import { Renderer } from './renderer';

class Game {
  private renderer: Renderer;
  private updateInterval: number | null = null;
  
  constructor() {
    this.renderer = new Renderer('app');
    this.start();
  }
  
  async start(): Promise<void> {
    // Initial fetch
    await this.updateGameState();
    
    // Set up polling every second
    this.updateInterval = window.setInterval(async () => {
      await this.updateGameState();
    }, 1000);
  }
  
  async updateGameState(): Promise<void> {
    try {
      const gameState = await Api.getGameState();
      this.renderer.render(gameState);
    } catch (error) {
      console.error('Error updating game state:', error);
    }
  }
  
  stop(): void {
    if (this.updateInterval !== null) {
      clearInterval(this.updateInterval);
      this.updateInterval = null;
    }
  }
}

// Start the game when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  new Game();
});
