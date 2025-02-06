import {Injectable} from '@angular/core';
import {Preferences} from '@capacitor/preferences';
import { Storage } from '@capacitor/storage';
import {User} from "../pages/account/account";

// Save JSON data
export class jsonData  {
  key: string
}

@Injectable({
  providedIn: 'root'
})
export class StorageService {
  constructor() { }

  async setData(key: string, data: User[] ) {
    let value: string = JSON.stringify(data);

    await Preferences.set({key: key, value: value}) ;
  }

  async getData(key: string) {
    return (await Preferences.get({key}))
  }

  async delData(key: string) {
    await Preferences.remove({key})
  }

  async upData(key: string, value: any) {
    await Preferences.set({key, value})
  }

  async clear() {
    await Preferences.clear()
  }

}
