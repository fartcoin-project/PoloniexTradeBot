import {Component, ElementRef, Input, OnChanges, OnDestroy, OnInit, SimpleChange, SimpleChanges, ViewChild} from '@angular/core';
import {
  Config,
  IonRouterOutlet,
  LoadingController,
  PopoverController
} from "@ionic/angular";

import {NavigationEnd, Router} from "@angular/router";
import {StorageService} from "../../services/storage.service";
import {AccountPage, User} from "../account/account";
import { Storage } from '@ionic/storage-angular';
import { Renderer2} from '@angular/core';
import "jquery";
import {VlcPopoverPage} from "./vlc-popover";
import {
  AlertController,
  ModalController,
  ToastController
} from "@ionic/angular";
import {Element} from "@angular/compiler";

import {GetResult} from "@capacitor/preferences";
import {ConferenceData} from "../../providers/conference-data";

import {UserData} from "../../providers/user-data";
import Echo from './echo-plugin';
import { HttpClient } from '@angular/common/http';

declare var $: JQueryStatic;
declare var jQuery: JQueryStatic;


@Component({
  selector: 'app-vlc',
  templateUrl: './vlc.component.html',
  styleUrls: ['./vlc.component.scss']
})
export class VlcComponent implements OnInit, OnChanges, OnDestroy {
  static hideIframe: string;
  @Input() vlcdata: User[]=  [];
  all: any;
  routerSubscription: any;
  apiKey: string = '';
  secretKey: string = '';
  budget: number = 0.0001;
  tradingPairs: any[] = [];
  orders: any[] = [];
  excludeList: string[] = [];
  log: string[] = [];

  constructor(
    public popoverCtrl: PopoverController,
    public loadingCtrl: LoadingController,
    public storageServive: StorageService,
    public router: Router,
    public routerOutlet: IonRouterOutlet,
    public config: Config,
    private renderer: Renderer2,
    public alertCtrl: AlertController,
    public confData: ConferenceData,
    public modalCtrl: ModalController,
    public toastCtrl: ToastController,
    public user: UserData,
    private http: HttpClient,
    private alertController: AlertController,
    private toastController: ToastController

  ) { }

  // This lifecycle method will be triggered when the Home page becomes active
  ionViewWillEnter() {
    this.refreshData(); // Replace this with your data-fetching or refreshing logic
  }

  refreshData() {
    this.getJson();
  }

  toggle($event: User) {
    this.vlcdata.find(value => {
      if (value.ipAddress === $event.ipAddress) value.hide = !value.hide;
    })
    console.log("$event: ", $event);
  }

  async getJson() {
      await this.storageServive.getData("VLC").then((data:any) => {
        let res: User[];
          res = JSON.parse(data.value);
          this.vlcdata = res
        console.log("%c 2 --> 73||C:/workspace/projects/Android-tradebot/src/app/pages/vlc/vlc.component.ts\n this.vlcdata: ","color:#0f0;", this.vlcdata);
      });
  }

  ngOnInit(): void {
    this.getJson();
    this.loadTradingPairs();
  }

  // This method will be triggered whenever @Input() properties change
  ngOnChanges(changes: SimpleChanges) {
    console.log('Changes detected:', changes);

    // Check if a specific property changed
    if (changes['vlcdata']) {
      const previousValue = changes['vlcdata'].previousValue;
      const currentValue = changes['vlcdata'].currentValue;
      console.log(`inputProp changed from ${previousValue} to ${currentValue}`);

    }
  }

  ngOnDestroy(): void {
    // Unsubscribe to avoid memory leaks

  }

  loadTradingPairs() {
    this.http.get('http://localhost:3000/api/trading-pairs').subscribe(
      (data: any) => {
        this.tradingPairs = data;
      },
      (error) => {
        console.error('Error fetching trading pairs', error);
      }
    );
  }

  startBot() {
    this.http.post('http://localhost:3000/api/start', {
      apiKey: this.apiKey,
      secretKey: this.secretKey,
      budget: this.budget,
      excludeList: this.excludeList,
    }).subscribe(
      async (res) => {
        const toast = await this.toastController.create({
          message: 'TradeBot started successfully!',
          duration: 2000,
          color: 'success',
        });
        await toast.present();
      },
      async (error) => {
        const alert = await this.alertController.create({
          header: 'Error',
          message: 'Failed to start the TradeBot.',
          buttons: ['OK'],
        });
        await alert.present();
      }
    );
  }

  stopBot() {
    this.http.post('http://localhost:3000/api/stop', {}).subscribe(
      async (res) => {
        const toast = await this.toastController.create({
          message: 'TradeBot stopped.',
          duration: 2000,
          color: 'danger',
        });
        await toast.present();
      }
    );
  }

  getOrders() {
    this.http.get('http://localhost:3000/api/orders').subscribe(
      (data: any) => {
        this.orders = data;
      },
      (error) => {
        console.error('Error fetching orders', error);
      }
    );
  }



  getPcName(buttenName: string): string {
    const pcMatch = buttenName.match(/\d+\.\d+\.\d+\.(\d+)/);  // Matches the last octet
    const portMatch = buttenName.match(/:(\d{4})/);  // Matches the first two digits of the port (81)
// Extract values if matches are found
    const pc = pcMatch ? pcMatch[1] : null;
    const port = portMatch ? portMatch[1].slice(-2) : null;

    let matchedText;
    if (pc && port) {
      matchedText = pc + ': ' + port;
    }
    return matchedText;
  }

  async presentPopover(event: Event) {
    const popover = await this.popoverCtrl.create({
      component: VlcPopoverPage,
      event
    });
    await popover.present();
  }
}
