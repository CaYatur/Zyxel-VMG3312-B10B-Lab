window.CAYA_LIVE_MODULES = [
  {
    "id": "connection-status",
    "title": "Ağ Haritası ve Durum",
    "category": "İzleme",
    "tabJson": null,
    "route": "/pages/connectionStatus/naviView_partialLoad.html",
    "risk": "normal",
    "pages": [
      {
        "label": "Durum",
        "url": "/pages/connectionStatus/naviView_partialLoad.html",
        "default": true
      }
    ]
  },
  {
    "id": "maintenance-configuration",
    "title": "Yapılandırma",
    "category": "Bakım",
    "tabJson": "../maintenance/configuration/tab.json",
    "route": "/pages/tabFW/tabFW.html?tabJson=../maintenance/configuration/tab.json&&tabIndex=0",
    "risk": "critical",
    "pages": [
      {
        "label": "Configuration",
        "url": "../maintenance/configuration/configuration.html",
        "default": false
      }
    ]
  },
  {
    "id": "maintenance-disagnostic",
    "title": "Tanılama",
    "category": "Bakım",
    "tabJson": "../maintenance/disagnostic/tab.json",
    "route": "/pages/tabFW/tabFW.html?tabJson=../maintenance/disagnostic/tab.json&&tabIndex=0",
    "risk": "caution",
    "pages": [
      {
        "label": "Ping, Traceroute ve Nslookup",
        "url": "../maintenance/disagnostic/pingTest.html",
        "default": false
      },
      {
        "label": "802.1ag",
        "url": "../maintenance/disagnostic/8021ag.html",
        "default": false
      },
      {
        "label": "OAM Ping",
        "url": "../maintenance/disagnostic/oamPing.html",
        "default": false
      }
    ]
  },
  {
    "id": "maintenance-firmwareupgrade",
    "title": "Yazılım Güncelleme",
    "category": "Bakım",
    "tabJson": "../maintenance/firmwareUpgrade/tab.json",
    "route": "/pages/tabFW/tabFW.html?tabJson=../maintenance/firmwareUpgrade/tab.json&&tabIndex=0",
    "risk": "critical",
    "pages": [
      {
        "label": "Firmware Upgrade",
        "url": "../maintenance/firmwareUpgrade/firmwareUpgrade.html",
        "default": false
      }
    ]
  },
  {
    "id": "maintenance-log",
    "title": "Günlük Ayarları",
    "category": "Bakım",
    "tabJson": "../maintenance/logSetting/tab.json",
    "route": "/pages/tabFW/tabFW.html?tabJson=../maintenance/logSetting/tab.json&&tabIndex=0",
    "risk": "caution",
    "pages": [
      {
        "label": "Log Setting",
        "url": "../maintenance/logSetting/logSetting.html",
        "default": false
      }
    ]
  },
  {
    "id": "maintenance-reboot",
    "title": "Yeniden Başlatma",
    "category": "Bakım",
    "tabJson": "../maintenance/reboot/tab.json",
    "route": "/pages/tabFW/tabFW.html?tabJson=../maintenance/reboot/tab.json&&tabIndex=0",
    "risk": "critical",
    "pages": [
      {
        "label": "Reboot",
        "url": "../maintenance/reboot/reboot.html",
        "default": false
      }
    ]
  },
  {
    "id": "maintenance-remoteMGMT",
    "title": "Uzaktan Yönetim",
    "category": "Bakım",
    "tabJson": "../maintenance/remoteMGMT/tab.json",
    "route": "/pages/tabFW/tabFW.html?tabJson=../maintenance/remoteMGMT/tab.json&&tabIndex=0",
    "risk": "caution",
    "pages": [
      {
        "label": "Uzaktan MGMT",
        "url": "../maintenance/remoteMGMT/remoteMGMT.html",
        "default": false
      },
      {
        "label": "Güvenilir Alan",
        "url": "../maintenance/remoteMGMT/trustdomain.html",
        "default": false
      }
    ]
  },
  {
    "id": "maintenance-time",
    "title": "Tarih ve Saat",
    "category": "Bakım",
    "tabJson": "../maintenance/time/tab.json",
    "route": "/pages/tabFW/tabFW.html?tabJson=../maintenance/time/tab.json&&tabIndex=0",
    "risk": "caution",
    "pages": [
      {
        "label": "Time",
        "url": "../maintenance/time/time.html",
        "default": false
      }
    ]
  },
  {
    "id": "maintenance-useraccount",
    "title": "Kullanıcı Hesapları",
    "category": "Bakım",
    "tabJson": "../maintenance/userAccount/tab.json",
    "route": "/pages/tabFW/tabFW.html?tabJson=../maintenance/userAccount/tab.json&&tabIndex=0",
    "risk": "caution",
    "pages": [
      {
        "label": "User Account",
        "url": "../maintenance/userAccount/userAccount.html",
        "default": false
      }
    ]
  },
  {
    "id": "network-broadband",
    "title": "Genişbant / WAN",
    "category": "Ağ",
    "tabJson": "../network/broadband/tab.json",
    "route": "/pages/tabFW/tabFW.html?tabJson=../network/broadband/tab.json&&tabIndex=0",
    "risk": "normal",
    "pages": [
      {
        "label": "Genişbant",
        "url": "../network/broadband/broadband.html",
        "default": false
      },
      {
        "label": "3G Yedekleme",
        "url": "../network/broadband/3gbackup.html",
        "default": false
      },
      {
        "label": "Gelişmiş",
        "url": "../network/broadband/advanced_cfg.html",
        "default": false
      }
    ]
  },
  {
    "id": "network-dns",
    "title": "DNS",
    "category": "Ağ",
    "tabJson": "../network/dns/tab.json",
    "route": "/pages/tabFW/tabFW.html?tabJson=../network/dns/tab.json&&tabIndex=0",
    "risk": "normal",
    "pages": [
      {
        "label": "DNS Girdisi",
        "url": "../network/dns/dns_entry.html",
        "default": false
      },
      {
        "label": "Dinamik DNS",
        "url": "../network/dns/dynamicDNS.html",
        "default": false
      }
    ]
  },
  {
    "id": "network-homeNetworking",
    "title": "Ev Ağı",
    "category": "Ağ",
    "tabJson": "../network/homeNetworking/tab.json",
    "route": "/pages/tabFW/tabFW.html?tabJson=../network/homeNetworking/tab.json&&tabIndex=0",
    "risk": "normal",
    "pages": [
      {
        "label": "Yerel Ağ Kurulumu",
        "url": "../network/homeNetworking/lanSetup.html",
        "default": false
      },
      {
        "label": "Statik DHCP",
        "url": "../network/homeNetworking/staticDHCP.html",
        "default": false
      },
      {
        "label": "UPnP",
        "url": "../network/homeNetworking/upnp.html",
        "default": false
      },
      {
        "label": "LAN VLAN",
        "url": "../network/homeNetworking/lanvlan.html",
        "default": false
      }
    ]
  },
  {
    "id": "network-interfacegroup",
    "title": "Arayüz Grupları",
    "category": "Ağ",
    "tabJson": "../network/intfGrp/tab.json",
    "route": "/pages/tabFW/tabFW.html?tabJson=../network/intfGrp/tab.json&&tabIndex=0",
    "risk": "normal",
    "pages": [
      {
        "label": "Interface Group",
        "url": "../network/intfGrp/intfGrp.html",
        "default": false
      }
    ]
  },
  {
    "id": "network-nat",
    "title": "NAT",
    "category": "Ağ",
    "tabJson": "../network/nat/tab.json",
    "route": "/pages/tabFW/tabFW.html?tabJson=../network/nat/tab.json&&tabIndex=0",
    "risk": "normal",
    "pages": [
      {
        "label": "Port Yönlendirme",
        "url": "../network/nat/portForwarding.html",
        "default": false
      },
      {
        "label": "Uygulamalar",
        "url": "../network/nat/applications.html",
        "default": false
      },
      {
        "label": "Port Tetikleme",
        "url": "../network/nat/portTriggering.html",
        "default": false
      },
      {
        "label": "DMZ",
        "url": "../network/nat/dmz.html",
        "default": false
      },
      {
        "label": "ALG",
        "url": "../network/nat/alg.html",
        "default": false
      },
      {
        "label": "Adres Eşleştirme",
        "url": "../network/nat/AddressMapping.html",
        "default": false
      },
      {
        "label": "NATLoopback",
        "url": "../network/nat/NATLoopbackCfg.html",
        "default": false
      }
    ]
  },
  {
    "id": "network-qos",
    "title": "QoS",
    "category": "Ağ",
    "tabJson": "../network/qos/tab.json",
    "route": "/pages/tabFW/tabFW.html?tabJson=../network/qos/tab.json&&tabIndex=0",
    "risk": "normal",
    "pages": [
      {
        "label": "Genel",
        "url": "../network/qos/general.html",
        "default": false
      },
      {
        "label": "Kuyruk Kurulumu",
        "url": "../network/qos/queue.html",
        "default": false
      },
      {
        "label": "Sınıf Kurulumu",
        "url": "../network/qos/classSetup.html",
        "default": false
      },
      {
        "label": "Kural Kurulumu",
        "url": "../network/qos/policer.html",
        "default": false
      },
      {
        "label": "İzle ",
        "url": "../network/qos/monitor.html",
        "default": false
      }
    ]
  },
  {
    "id": "network-routing",
    "title": "Yönlendirme",
    "category": "Ağ",
    "tabJson": "../network/routing/tab.json",
    "route": "/pages/tabFW/tabFW.html?tabJson=../network/routing/tab.json&&tabIndex=0",
    "risk": "normal",
    "pages": [
      {
        "label": "Statik Yönlendirme",
        "url": "../network/routing/static.html",
        "default": false
      },
      {
        "label": "Kurallı Yönlendirme",
        "url": "../network/routing/policyForwardCfg.html",
        "default": false
      },
      {
        "label": "RIP",
        "url": "../network/routing/rip.html",
        "default": false
      }
    ]
  },
  {
    "id": "network-usbservice",
    "title": "USB Servisleri",
    "category": "Ağ",
    "tabJson": "../network/usbService/tab.json",
    "route": "/pages/tabFW/tabFW.html?tabJson=../network/usbService/tab.json&&tabIndex=0",
    "risk": "normal",
    "pages": [
      {
        "label": "Dosya Paylaşımı",
        "url": "../network/usbService/fileSharing.html",
        "default": false
      },
      {
        "label": "Medya Sunucusu",
        "url": "../network/usbService/mediaServer.html",
        "default": false
      },
      {
        "label": "Yazdırma Sunucusu",
        "url": "../network/usbService/printServer.html",
        "default": false
      }
    ]
  },
  {
    "id": "network-wireless",
    "title": "Kablosuz Ağ",
    "category": "Ağ",
    "tabJson": "../network/wireless/tab.json",
    "route": "/pages/tabFW/tabFW.html?tabJson=../network/wireless/tab.json&&tabIndex=0",
    "risk": "normal",
    "pages": [
      {
        "label": "Genel",
        "url": "../network/wireless/wireless-load.wl?wlSsidIdx=0",
        "default": false
      },
      {
        "label": "Daha fazla AP",
        "url": "../network/wireless/moreAP.html",
        "default": false
      },
      {
        "label": "MAC Kimlik Doğrulama",
        "url": "../network/wireless/MACAuthentication.html",
        "default": false
      },
      {
        "label": "WPS",
        "url": "../network/wireless/wireless-wpsload.wl?wlSsidIdx=0",
        "default": false
      },
      {
        "label": "WMM",
        "url": "../network/wireless/wmm.html",
        "default": false
      },
      {
        "label": "WDS",
        "url": "../network/wireless/wds.html",
        "default": false
      },
      {
        "label": "Diğer",
        "url": "../network/wireless/others.html",
        "default": false
      },
      {
        "label": "Kanal Durumu",
        "url": "../network/wireless/wlan_channelstatus.html",
        "default": false
      }
    ]
  },
  {
    "id": "security-certificates",
    "title": "Sertifikalar",
    "category": "Güvenlik",
    "tabJson": "../security/certificates/tab.json",
    "route": "/pages/tabFW/tabFW.html?tabJson=../security/certificates/tab.json&&tabIndex=0",
    "risk": "normal",
    "pages": [
      {
        "label": "Yerel Sertifikalar",
        "url": "../security/certificates/localCertificates.html",
        "default": false
      },
      {
        "label": "Güvenilir CA",
        "url": "../security/certificates/trustedCA.html",
        "default": false
      }
    ]
  },
  {
    "id": "security-firewall",
    "title": "Güvenlik Duvarı",
    "category": "Güvenlik",
    "tabJson": "../security/firewall/tab.json",
    "route": "/pages/tabFW/tabFW.html?tabJson=../security/firewall/tab.json&&tabIndex=0",
    "risk": "normal",
    "pages": [
      {
        "label": "Genel",
        "url": "../security/firewall/firewall.html",
        "default": false
      },
      {
        "label": "Hizmet",
        "url": "../security/firewall/protocol.html",
        "default": false
      },
      {
        "label": "Erişim Kontrolü",
        "url": "../security/firewall/accessControl.html",
        "default": false
      },
      {
        "label": "DoS",
        "url": "../security/firewall/DosCfg.html",
        "default": false
      }
    ]
  },
  {
    "id": "security-ipsecVPN",
    "title": "IPSec VPN",
    "category": "Güvenlik",
    "tabJson": "../security/ipsecVPN/tab.json",
    "route": "/pages/tabFW/tabFW.html?tabJson=../security/ipsecVPN/tab.json&&tabIndex=0",
    "risk": "normal",
    "pages": [
      {
        "label": "Kurulum",
        "url": "../security/ipsecVPN/ipsec.html",
        "default": false
      },
      {
        "label": "İzle ",
        "url": "../security/ipsecVPN/ipsec_status.html",
        "default": false
      }
    ]
  },
  {
    "id": "security-macfilter",
    "title": "MAC Filtresi",
    "category": "Güvenlik",
    "tabJson": "../security/macFilter/tab.json",
    "route": "/pages/tabFW/tabFW.html?tabJson=../security/macFilter/tab.json&&tabIndex=0",
    "risk": "normal",
    "pages": [
      {
        "label": "MAC Filter",
        "url": "../security/macFilter/macFilter.html",
        "default": false
      }
    ]
  },
  {
    "id": "security-parentalcontrol",
    "title": "Ebeveyn Kontrolü",
    "category": "Güvenlik",
    "tabJson": "../security/parentalControl/tab.json",
    "route": "/pages/tabFW/tabFW.html?tabJson=../security/parentalControl/tab.json&&tabIndex=0",
    "risk": "normal",
    "pages": [
      {
        "label": "Parental Control",
        "url": "../security/parentalControl/parentalControl.html",
        "default": false
      }
    ]
  },
  {
    "id": "security-scheduler",
    "title": "Zamanlayıcı Kuralları",
    "category": "Güvenlik",
    "tabJson": "../security/schedulerRule/tab.json",
    "route": "/pages/tabFW/tabFW.html?tabJson=../security/schedulerRule/tab.json&&tabIndex=0",
    "risk": "normal",
    "pages": [
      {
        "label": "Scheduler Rules",
        "url": "../security/schedulerRule/schedulerRule.html",
        "default": false
      }
    ]
  },
  {
    "id": "systemMonitoring-3g",
    "title": "3G İstatistikleri",
    "category": "İzleme",
    "tabJson": "../systemMonitoring/3gStatistics/tab.json",
    "route": "/pages/tabFW/tabFW.html?tabJson=../systemMonitoring/3gStatistics/tab.json&&tabIndex=0",
    "risk": "normal",
    "pages": [
      {
        "label": "3g Statistics",
        "url": "../systemMonitoring/3gStatistics/3gStatistics.html",
        "default": false
      }
    ]
  },
  {
    "id": "systemMonitoring-arp",
    "title": "ARP Tablosu",
    "category": "İzleme",
    "tabJson": "../systemMonitoring/arpTable/tab.json",
    "route": "/pages/tabFW/tabFW.html?tabJson=../systemMonitoring/arpTable/tab.json&&tabIndex=0",
    "risk": "normal",
    "pages": [
      {
        "label": "ARP Table",
        "url": "../systemMonitoring/arpTable/arp_monitor.html",
        "default": false
      }
    ]
  },
  {
    "id": "systemMonitoring-igmp",
    "title": "IGMP Grup Durumu",
    "category": "İzleme",
    "tabJson": "../systemMonitoring/igmpGroupStatus/tab.json",
    "route": "/pages/tabFW/tabFW.html?tabJson=../systemMonitoring/igmpGroupStatus/tab.json&&tabIndex=0",
    "risk": "normal",
    "pages": [
      {
        "label": "IGMP Group",
        "url": "../systemMonitoring/igmpGroupStatus/igmpGroupStatus-status.cmd",
        "default": false
      }
    ]
  },
  {
    "id": "systemMonitoring-log",
    "title": "Günlükler",
    "category": "İzleme",
    "tabJson": "../systemMonitoring/log/tab.json",
    "route": "/pages/tabFW/tabFW.html?tabJson=../systemMonitoring/log/tab.json&&tabIndex=0",
    "risk": "normal",
    "pages": [
      {
        "label": "Sistem Günlüğü",
        "url": "../systemMonitoring/log/log-systemLog.cmd",
        "default": false
      },
      {
        "label": "Güvenlik Günlüğü",
        "url": "../systemMonitoring/log/log-securityLog.cmd",
        "default": false
      }
    ]
  },
  {
    "id": "systemMonitoring-routeTable",
    "title": "Yönlendirme Tablosu",
    "category": "İzleme",
    "tabJson": "../systemMonitoring/routeTable/tab.json",
    "route": "/pages/tabFW/tabFW.html?tabJson=../systemMonitoring/routeTable/tab.json&&tabIndex=0",
    "risk": "normal",
    "pages": [
      {
        "label": "RouteTable",
        "url": "../systemMonitoring/routeTable/routeTable.html",
        "default": false
      }
    ]
  },
  {
    "id": "systemMonitoring-traffic",
    "title": "Trafik Durumu",
    "category": "İzleme",
    "tabJson": "../systemMonitoring/trafficStatus/tab.json",
    "route": "/pages/tabFW/tabFW.html?tabJson=../systemMonitoring/trafficStatus/tab.json&&tabIndex=0",
    "risk": "normal",
    "pages": [
      {
        "label": "WAN",
        "url": "../systemMonitoring/trafficStatus/wan.html",
        "default": false
      },
      {
        "label": "Yerel Ağ",
        "url": "../systemMonitoring/trafficStatus/lan.html",
        "default": false
      }
    ]
  },
  {
    "id": "systemMonitoring-xdsl",
    "title": "xDSL İstatistikleri",
    "category": "İzleme",
    "tabJson": "../systemMonitoring/xdslStatistics/tab.json",
    "route": "/pages/tabFW/tabFW.html?tabJson=../systemMonitoring/xdslStatistics/tab.json&&tabIndex=0",
    "risk": "normal",
    "pages": [
      {
        "label": "xDSL Statistics",
        "url": "../systemMonitoring/xdslStatistics/xdslStatistics.html",
        "default": false
      }
    ]
  }
];
