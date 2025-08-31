package pkg

import (
	"context"
	"fmt"
	"helmblog/services/auth/pkg/db"
	"net/http"
	"time"

	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/nats-io/nats.go"
	"github.com/nats-io/nats.go/jetstream"
)

type AppState struct{
  Adaptors *db.Queries
	Nc *nats.Conn
	Stream jetstream.Stream
}

func NewState() (*AppState, error){
	ctx, done := context.WithTimeout(context.Background(), time.Millisecond*time.Duration(settings.ConnTimeout))
	defer done()
	dbPool, err := pgxpool.New(ctx, settings.DatabaseUrl)
	if err != nil{
		return nil, fmt.Errorf("DB connection failed: %v", err)
	}
	nc, err := nats.Connect(settings.NatsBrokerUrl)
	if err != nil{
		return nil, fmt.Errorf("Nats connection failed: %v", err)
	}
	js, err := jetstream.New(nc)
	if err != nil{
		return nil, fmt.Errorf("ERR-NATS-JS: %v", err)
	}
	streamConfig := jetstream.StreamConfig{
		Name: "messages",
		Subjects: []string{"msg.>"},
	}
	stream, err := js.CreateOrUpdateStream(ctx, streamConfig)
	return &AppState{Adaptors: db.New(dbPool), Nc: nc, Stream: stream}, nil
}

type Server struct{
	port int
	state *AppState
}

func NewServer() *Server{
	LoadSettings()
	return &Server{port: settings.ListenPort}
}

func (s *Server) Start() {
	http.HandleFunc("POST /auth/login", NewSession)
	http.HandleFunc("POST /authn", Authenticate)
	http.HandleFunc("POST /authz", Authorize)
	fmt.Printf("listening at %d\n", s.port)
	http.ListenAndServe(fmt.Sprintf(":%d", s.port), nil)
}


