import { Component, OnInit, ViewEncapsulation } from '@angular/core';
import { SwUpdate } from '@angular/service-worker';
import { ToastController } from '@ionic/angular';
import {GetResult, Preferences} from '@capacitor/preferences';
import { Storage } from '@ionic/storage-angular';
import {SharedPrefsPlugin} from "shared-prefs-plugin/src";
import {Capacitor} from "@capacitor/core";



@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss'],
  encapsulation: ViewEncapsulation.None
})
export class AppComponent implements OnInit {
  appPages = [
    {
      title: 'vlc',
      url: '/app/tabs/vlc',
      icon: 'easel'
    },
    {
      title: 'Account',
      url: '/app/tabs/account',
      icon: 'people'
    }
  ];

  dark = true;
  title = this.appPages
  passvalue: string;

  constructor(
    private storage: Storage,
    private swUpdate: SwUpdate,
    private toastCtrl: ToastController,
  ) {
    this.initializeApp();
  }



  async ngOnInit() {
    await this.storage.create();
    console.log(SharedPrefsPlugin);
    this.swUpdate.versionUpdates.subscribe(async res => {
      const toast = await this.toastCtrl.create({
        message: 'Update available!',
        position: 'bottom',
        buttons: [
          {
            role: 'cancel',
            text: 'Reload'
          }
        ]
      });

      await toast.present();

      toast
        .onDidDismiss()
        .then(() => this.swUpdate.activateUpdate())
        .then(() => window.location.reload());
    });
    // Use matchMedia to check the user preference
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)');
    console.log("%c 1 --> 54||app.component.ts\n prefersDark: ","color:#f0f;", prefersDark);

    // Initialize the dark theme based on the initial
    // value of the prefers-color-scheme media query
    this.initializeDarkTheme(prefersDark.matches);

    // Listen for changes to the prefers-color-scheme media query
    prefersDark.addEventListener('change', (mediaQuery) => this.initializeDarkTheme(mediaQuery.matches));
  }

  initializeApp() {
    const getConfig = async () => {
      return  await Preferences.get({ key: 'pass' });
    };

    const setDefaultConfig = async () => {
      if (!this.passvalue) {
        this.passvalue = prompt('Please enter your VLC password: ', '') || '1z2x';
        {
          await Preferences.set({
            key: 'pass',
            value: this.passvalue,
          });
        }
      }
    };

    function checkConfig(r) {
      console.log("checking passvalue")
      console.log(r)
      if (r == null) {
        setDefaultConfig().then(r => getConfig());
      } else {
        console.log("Value: ", r)
      }
    }

    getConfig().then(r => checkConfig(r) );

    if (Capacitor.getPlatform() === 'android') {
      retrievePassValue().then(r => console.log("Value: ", r));
      async function retrievePassValue() {
        try {
          const result = await SharedPrefsPlugin.getPreference({key: 'pass'});
          console.log('Pass value from Android:', result.value);
        }
        catch (error) {
          console.error('Error fetching pass value:', error);
        }
      }
    }
  }

  // Check/uncheck the toggle and update the theme based on isDark
  initializeDarkTheme(isDark) {
    this.dark = isDark;
    this.toggleDarkTheme(isDark);
  }

  // Listen for the toggle check/uncheck to toggle the dark theme
  toggleChange(ev) {
    this.toggleDarkTheme(ev.detail.checked);
  }

  // Add or remove the "dark" class on the document body
  toggleDarkTheme(shouldAdd) {
    document.body.classList.toggle('dark', shouldAdd);
  }
}
