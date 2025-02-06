import { Injectable } from '@angular/core';

@Injectable({ providedIn: 'root' })
export class UserService {

  private _ipAddress: string;
  private _hide: boolean;


  get ipAddress() {
    return this._ipAddress;
  }

  set ipAddress(ip: string) {
    this._ipAddress = ip;
  }

  get hide() {
    return this._hide;
  }

  set hide(hide: boolean) {
    this._hide = hide;
  }
}
