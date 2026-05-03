// ============================================================================
// stepper.js — drives an algorithm generator with play/pause/step controls
// ============================================================================

export class Stepper {
  constructor() {
    this.gen = null;
    this.onState = null;
    this.onDone = null;
    this.onStatus = null;
    this.playing = false;
    this.done = false;
    this.lastState = null;
    this.finalResult = null;
    this.speedMs = 60;
    this.stepCount = 0;
    this._tickHandle = null;
  }

  /**
   * @param {Generator|AsyncGenerator} generator
   * @param {{onState, onDone, onStatus}} cbs
   */
  load(generator, cbs = {}) {
    this.cancel();
    this.gen = generator;
    this.onState = cbs.onState;
    this.onDone = cbs.onDone;
    this.onStatus = cbs.onStatus;
    this.playing = false;
    this.done = false;
    this.lastState = null;
    this.finalResult = null;
    this.stepCount = 0;
    this._notifyStatus('loaded');
  }

  cancel() {
    this._stopTick();
    this.gen = null;
    this.playing = false;
    this.done = true;
    this._notifyStatus('idle');
  }

  /** advance one yield. returns true if more steps remain */
  async step() {
    if (!this.gen || this.done) return false;
    let res;
    try {
      res = await this.gen.next();
    } catch (e) {
      console.error(e);
      this.done = true;
      this._notifyStatus('error', String(e?.message || e));
      return false;
    }
    if (res.done) {
      this.done = true;
      this.finalResult = res.value || null;
      if (this.finalResult) {
        this.lastState = { ...this.lastState, ...this.finalResult, phase: 'done' };
        this.onState?.(this.lastState);
      }
      this.onDone?.(this.finalResult);
      this._notifyStatus('done');
      this._stopTick();
      return false;
    }
    this.stepCount++;
    this.lastState = res.value;
    this.onState?.(res.value);
    return true;
  }

  play() {
    if (!this.gen || this.done || this.playing) return;
    this.playing = true;
    this._notifyStatus('running');
    this._tick();
  }

  pause() {
    this.playing = false;
    this._stopTick();
    this._notifyStatus('paused');
  }

  setSpeed(ms) {
    this.speedMs = Math.max(0, ms | 0);
    if (this.playing) {
      this._stopTick();
      this._tick();
    }
  }

  /** advance up to n steps as fast as possible */
  async fastForward(n = 100) {
    for (let i = 0; i < n; i++) {
      const ok = await this.step();
      if (!ok) break;
    }
  }

  /** advance until done */
  async runToEnd(maxSteps = 200000) {
    let i = 0;
    while (!this.done && i < maxSteps) {
      const ok = await this.step();
      if (!ok) break;
      i++;
      if (i % 200 === 0) await new Promise(r => setTimeout(r, 0)); // yield to UI
    }
  }

  // ----- private ------------------------------------------------------------

  _tick() {
    const loop = async () => {
      if (!this.playing || this.done) return;
      await this.step();
      if (this.playing && !this.done) {
        this._tickHandle = setTimeout(loop, this.speedMs);
      }
    };
    this._tickHandle = setTimeout(loop, this.speedMs);
  }

  _stopTick() {
    if (this._tickHandle != null) {
      clearTimeout(this._tickHandle);
      this._tickHandle = null;
    }
  }

  _notifyStatus(status, extra) {
    this.onStatus?.(status, extra);
  }
}
