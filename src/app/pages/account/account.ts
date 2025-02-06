import {Component, OnInit} from '@angular/core';
import {Router, RouterLink} from '@angular/router';
import {AlertController, ItemReorderEventDetail} from '@ionic/angular';
import { UserData } from '../../providers/user-data';
import {IonicModule, NavController} from '@ionic/angular';
import {
  FormGroup,
  FormControl,
  FormBuilder,
  ReactiveFormsModule,
  FormsModule, ValidatorFn, AbstractControl, ValidationErrors
} from '@angular/forms';
import {JsonPipe, NgForOf, NgIf} from "@angular/common";
import {UserService} from "../../services/user.service";
import {StorageService} from "../../services/storage.service";
import {Preferences} from "@capacitor/preferences";
import {SharedPrefsPlugin} from "shared-prefs-plugin/src";
import {Capacitor} from "@capacitor/core";

export interface pass {
  tradebotPass: string,
}

export interface User {
  icon?: string;
  buttenName?: string;
  hide: boolean;
  ipAddress: string;
}


@Component({
  selector: 'page-account',
  templateUrl: 'account.html',
  styleUrls: ['./account.scss'],
  standalone: true,
  imports: [
    IonicModule,
    ReactiveFormsModule,
    JsonPipe,
    NgIf,
    NgForOf,
    FormsModule,
    RouterLink
  ],
})
export class AccountPage implements OnInit {
  username: string;
  ipaddress: string;
  tradebotpassword: string;
  myForm: FormGroup;
  user: User;
  addTradebot: User;

  userSettings: User[] = [{
    ipAddress: '192.168.2.2:8080', hide: false
  }, {
    ipAddress: '192.168.2.2:8081', hide: false
  }];


  public getterdata: User[] = [];
  configForm: any;
  tradebotPass: string = '';

  constructor(
    private userService: UserService,
    public storageServive: StorageService,
    public alertCtrl: AlertController,
    public router: Router,
    public userData: UserData,
    public navCtrl: NavController,
    private fb: FormBuilder) {
  }

  ngOnInit() {

    this.getJson(1);
    this.user = this.userService;
    this.configForm = this.userService;

    //1. FormBuilder
    this.myForm = this.fb.group({
      ipAddress: ['', this.ipValidator],
    });

    // 2. FormControl, FormGroup,
    this.myForm = new FormGroup({
      ipAddress: new FormControl('', this.ipValidator),
    });

    this.userSettings = [...this.userSettings, this.addTradebot]
  }

  setHide(i: number) {
    this.getterdata[i].hide = !this.getterdata[i].hide;
    this.setJson(1);
  }

  setJson(setter: number) {
    if (setter == 1) {
      this.getJson(setter).then(r => console.log("getting before setting: "));

      let ip = [{
        'ipAddress': 'http://192.168.2.' + this.user.ipAddress + '/mobile.html',
        'hide': this.user.hide || false
      }]
      if (this.getterdata.find(value => value.ipAddress === ip[0].ipAddress)) {
        console.log("%c 1 --> something: ", "color:#f0f;");
      } else if (this.user.ipAddress === undefined) {
        console.log("%c 2 --> 114||C:/workspace/projects/Android-tradebot/src/app/pages/account/account.ts\n this.user.ipAddress: ", "color:#0f0;", this.user.ipAddress);
      } else {
        this.getterdata = [
          ...this.getterdata,
          ...ip
        ].filter(value => value.ipAddress)
      }
      let configAccount: User[] = this.getterdata;
      this.storageServive.setData("TRADEBOT", configAccount).then(r => {
      });
      // this.storageServive.setData('pass', config).then(r =>{});

    }

    this.getJson(setter).then(r => console.log("getting after setting: "));

  }

  async getJson(getter: number) {
    if (getter == 1) {
      await this.storageServive.getData("TRADEBOT").then((data: any) => {

        let res;
        if (data.value) {
          res = JSON.parse(data.value);

          this.getterdata = res

          console.log("%c 1 --> 135||C:/workspace/projects/Android-tradebot/src/app/pages/account/account.ts\n this.getterdata: ", "color:#f0f;", this.getterdata);
        }
      });
    }

  }

  async delJson(i) {
    await this.storageServive.delData("TRADEBOT");
    let foo_object = this.getterdata[i];
    this.getterdata = this.getterdata.filter(obj => {
      return obj !== foo_object
    });
  }

  async getPass(x) {
    if (x === 1) {
      if (Capacitor.getPlatform() === 'android') {
        const result = await SharedPrefsPlugin.getPreference({ key: 'pass' });
        this.tradebotPass = result.value || 'no password'
        console.log('Pass value from Android:', result.value);
      } else {
        const result = await Preferences.get({key: 'pass'})
        this.tradebotPass = result.value || 'no password'
        console.log('Pass value from Web:', result.value);
      }
    }

    if (x === 2) {
      if (Capacitor.getPlatform() === 'android') {
        await SharedPrefsPlugin.setPreference({
          key: 'pass',
          value: this.tradebotPass || '1z2x'
        });
      } else {
        await Preferences.set({
          key: 'pass',
          value: this.tradebotPass || '1z2x',
        });
      }
    }
  }

  ipValidator(ipAddress: FormControl): ValidatorFn {
    return (control: AbstractControl): ValidationErrors | null => {
      const regex = /^(?:\d{1,3}\.){3}\d{1,3}:(?:6553[0-5]|655[0-2]\d|65[0-4]\d{2}|6[0-4]\d{3}|[1-5]\d{4}|\d{1,4})$/;
      const valid = regex.test(ipAddress.value);
      return valid ? null : {ipAddress: valid}
    };
  }
}
