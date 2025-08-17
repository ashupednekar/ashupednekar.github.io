package pkg

import (
	"fmt"
	"sync"

	"go-simpler.org/env"
)


type Settings struct{
	ListenPort int `env:"LISTEN_PORT"`
	ConnTimeout int `env:"CONN_TIMEOUT"`
	DatabaseUrl string `env:"DATABASE_URL"`
	NatsBrokerUrl string `env:"NATS_BROKER_URL"`
}

var (
	settings *Settings
	once sync.Once
)

func LoadSettings() *Settings{
	once.Do(func(){
		s := Settings{}
		err := env.Load(&s, nil)
	  if err != nil{
			fmt.Printf("%s", err)
		}
		settings = &s
	})
	return settings
}
