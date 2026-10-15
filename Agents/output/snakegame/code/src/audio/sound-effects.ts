export class SoundEffects {
  private context: AudioContext | null = null;
  unlock(): void {
    if (!this.context) {
      const AudioContextClass = window.AudioContext;
      if (AudioContextClass) this.context = new AudioContextClass();
    }
    if (this.context?.state === 'suspended') void this.context.resume();
  }
  private tone(frequency: number, duration: number, type: OscillatorType = 'sine'): void {
    this.unlock();
    if (!this.context) return;
    const oscillator = this.context.createOscillator();
    const gain = this.context.createGain();
    oscillator.type = type; oscillator.frequency.value = frequency;
    gain.gain.setValueAtTime(0.08, this.context.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, this.context.currentTime + duration);
    oscillator.connect(gain); gain.connect(this.context.destination);
    oscillator.start(); oscillator.stop(this.context.currentTime + duration);
  }
  playEat(): void { this.tone(620, 0.08); }
  playGameOver(): void { this.tone(180, 0.35, 'triangle'); }
}
